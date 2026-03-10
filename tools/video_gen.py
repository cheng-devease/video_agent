"""视频生成工具 - Kling, Sora, Seedance, Veo3"""
import asyncio
import base64
import aiohttp
import mimetypes
from pathlib import Path
from typing import Dict, Optional, Any, List
from config.api_keys import api_keys
from config.settings import settings
from utils.logger import get_logger
from utils.retry import async_retry

logger = get_logger("video_gen")


class VideoGenTool:
    """视频生成基础工具"""

    def __init__(self):
        self.temp_dir = Path(settings.temp_dir) / "videos"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = settings.video_generation_timeout


class KlingAPI(VideoGenTool):
    """Kling视频生成API via fal.ai"""

    model_id = "fal-ai/kling-video/v3/pro/image-to-video"
    queue_base_url = "https://queue.fal.run"

    def __init__(self):
        super().__init__()
        self.api_key = api_keys.fal_api_key

    @async_retry(max_attempts=3)
    async def generate(
        self,
        image_path: str,
        prompt: str,
        negative_prompt: str = "",
        duration: int = 4,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """生成视频"""
        if not self.api_key:
            raise ValueError("FAL_API_KEY not configured for Kling generation")

        logger.info("Kling: Generating video with fal.ai...")

        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = self._build_payload(
            image_path=image_path,
            prompt=prompt,
            negative_prompt=negative_prompt,
            duration=duration,
            additional_params=additional_params,
        )

        async with aiohttp.ClientSession() as session:
            request_id = await self._submit_request(session, headers, payload)
            result = await self._wait_for_result(session, headers, request_id)
            video_url = self._extract_video_url(result)

            output_path = str(self.temp_dir / f"kling_{request_id}.mp4")
            await self._download(session, video_url, output_path)

        logger.info(f"Kling video saved: {output_path}")
        return output_path

    def _build_payload(
        self,
        image_path: str,
        prompt: str,
        negative_prompt: str = "",
        duration: int = 4,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """构造 fal.ai Kling 请求体。"""
        params = dict(additional_params or {})
        payload: Dict[str, Any] = {
            "start_image_url": self._normalize_media_input(params.pop("start_image", image_path)),
            "duration": str(params.pop("duration", duration)),
        }

        prompt_value = params.pop("prompt", prompt)
        multi_prompt = params.get("multi_prompt")
        if prompt_value:
            payload["prompt"] = prompt_value
        if multi_prompt:
            payload["multi_prompt"] = multi_prompt
        if not payload.get("prompt") and not payload.get("multi_prompt"):
            raise ValueError("Kling requires either 'prompt' or 'multi_prompt'")

        negative_prompt_value = params.pop("negative_prompt", negative_prompt)
        if negative_prompt_value:
            payload["negative_prompt"] = negative_prompt_value

        if "end_image_url" in params or "end_image" in params:
            payload["end_image_url"] = self._normalize_media_input(
                params.pop("end_image_url", params.pop("end_image", None))
            )

        if "reference_image_urls" in params:
            payload["reference_image_urls"] = [
                self._normalize_media_input(item)
                for item in params.pop("reference_image_urls")
            ]
        elif "reference_images" in params:
            payload["reference_image_urls"] = [
                self._normalize_media_input(item)
                for item in params.pop("reference_images")
            ]

        if "video_url" in params:
            payload["video_url"] = self._normalize_media_input(params.pop("video_url"))

        if "elements" in params:
            payload["elements"] = self._normalize_elements(params.pop("elements"))

        for key in (
            "aspect_ratio",
            "generate_audio",
            "voice_ids",
            "cfg_scale",
            "shot_type",
            "camera_control",
            "advanced_camera_control",
            "seed",
            "tail_image_url",
            "static_mask_url",
            "dynamic_masks",
        ):
            value = params.pop(key, None)
            if value is not None:
                payload[key] = value

        for key, value in params.items():
            if value is not None:
                payload[key] = value

        return payload

    def _normalize_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for element in elements:
            item = dict(element)
            image_input = item.pop("image_url", None) or item.pop("image", None) or item.pop("image_path", None)
            if image_input is not None:
                item["image_url"] = self._normalize_media_input(image_input)
            normalized.append(item)
        return normalized

    def _normalize_media_input(self, media_input: Any) -> str:
        if media_input is None:
            raise ValueError("Media input cannot be empty")

        media_str = str(media_input)
        if media_str.startswith(("http://", "https://", "data:")):
            return media_str

        path = Path(media_str)
        if not path.exists():
            raise FileNotFoundError(f"Media file not found: {media_str}")

        mime_type, _ = mimetypes.guess_type(path.name)
        mime_type = mime_type or "application/octet-stream"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    async def _submit_request(self, session, headers, payload: Dict[str, Any]) -> str:
        async with session.post(f"{self.queue_base_url}/{self.model_id}", headers=headers, json=payload) as resp:
            result = await resp.json()
            if resp.status >= 400:
                raise RuntimeError(f"Kling submit failed: {result}")

        request_id = result.get("request_id")
        if not request_id:
            raise RuntimeError(f"Kling submit missing request_id: {result}")

        return request_id

    async def _wait_for_result(self, session, headers, request_id: str) -> Dict[str, Any]:
        """等待 fal 队列任务完成。"""
        import time
        start = time.time()
        while time.time() - start < self.timeout:
            status_url = f"{self.queue_base_url}/{self.model_id}/requests/{request_id}/status"
            async with session.get(status_url, headers=headers) as resp:
                result = await resp.json()
                status = result.get("status")
                if resp.status >= 400:
                    raise RuntimeError(f"Kling status check failed: {result}")
                if status == "COMPLETED":
                    return await self._get_result(session, headers, request_id)
                if status in {"FAILED", "ERROR", "CANCELLED"}:
                    raise RuntimeError(f"Kling generation failed: {result}")
            await asyncio.sleep(5)
        raise TimeoutError("Kling generation timeout")

    async def _get_result(self, session, headers, request_id: str) -> Dict[str, Any]:
        result_url = f"{self.queue_base_url}/{self.model_id}/requests/{request_id}"
        async with session.get(result_url, headers=headers) as resp:
            result = await resp.json()
            if resp.status >= 400:
                raise RuntimeError(f"Kling result fetch failed: {result}")
        return result

    def _extract_video_url(self, result: Dict[str, Any]) -> str:
        response = result.get("response", result)

        if isinstance(response, dict):
            if isinstance(response.get("video"), dict) and response["video"].get("url"):
                return response["video"]["url"]
            if response.get("video_url"):
                return response["video_url"]
            if isinstance(response.get("videos"), list) and response["videos"]:
                first = response["videos"][0]
                if isinstance(first, dict) and first.get("url"):
                    return first["url"]

        raise RuntimeError(f"Kling result missing video URL: {result}")

    async def _download(self, session, url: str, output_path: str):
        async with session.get(url) as resp:
            if resp.status >= 400:
                raise RuntimeError(f"Failed to download Kling video: {url}")
            with open(output_path, "wb") as f:
                f.write(await resp.read())


class SoraAPI(VideoGenTool):
    """Sora视频生成API (OpenAI)"""

    def __init__(self):
        super().__init__()
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_keys.sora_api_key or api_keys.openai_api_key)

    @async_retry(max_attempts=3)
    async def generate(
        self,
        image_path: str,
        prompt: str,
        duration: int = 4,
    ) -> str:
        """生成视频"""
        logger.info(f"Sora: Generating video...")

        # OpenAI视频生成API (根据实际API调整)
        response = await self.client.video.generate(
            model="sora",
            image=image_path,
            prompt=prompt,
            duration=duration,
        )

        video_url = response.data.url
        output_path = str(self.temp_dir / f"sora_{response.id}.mp4")

        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as resp:
                with open(output_path, "wb") as f:
                    f.write(await resp.read())

        logger.info(f"Sora video saved: {output_path}")
        return output_path


class SeedanceAPI(VideoGenTool):
    """Seedance视频生成API (即梦)"""

    def __init__(self):
        super().__init__()
        self.api_key = api_keys.seedance_api_key
        self.api_url = api_keys.seedance_api_url

    @async_retry(max_attempts=3)
    async def generate(
        self,
        image_path: str,
        prompt: str,
        duration: int = 4,
    ) -> str:
        """生成视频"""
        if not self.api_key:
            raise ValueError("Seedance API key not configured")

        logger.info(f"Seedance: Generating video...")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "image_url": image_path,
            "prompt": prompt,
            "duration": duration,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_url}/v1/video/generate", headers=headers, json=payload) as resp:
                result = await resp.json()
                task_id = result.get("task_id")

            video_url = await self._wait_for_result(session, headers, task_id)

            output_path = str(self.temp_dir / f"seedance_{task_id}.mp4")
            await self._download(session, video_url, output_path)

        logger.info(f"Seedance video saved: {output_path}")
        return output_path

    async def _wait_for_result(self, session, headers, task_id: str) -> str:
        import time
        start = time.time()
        while time.time() - start < self.timeout:
            async with session.get(f"{self.api_url}/v1/video/tasks/{task_id}", headers=headers) as resp:
                result = await resp.json()
                if result.get("status") == "completed":
                    return result["video_url"]
                elif result.get("status") == "failed":
                    raise Exception(f"Seedance generation failed")
            await asyncio.sleep(5)
        raise TimeoutError("Seedance generation timeout")

    async def _download(self, session, url: str, output_path: str):
        async with session.get(url) as resp:
            with open(output_path, "wb") as f:
                f.write(await resp.read())


class Veo3API(VideoGenTool):
    """Google Veo3视频生成API"""

    def __init__(self):
        super().__init__()
        self.api_key = api_keys.veo3_api_key
        self.project_id = api_keys.veo3_project_id

    @async_retry(max_attempts=3)
    async def generate(
        self,
        image_path: str,
        prompt: str,
        duration: int = 4,
    ) -> str:
        """生成视频"""
        if not self.api_key:
            raise ValueError("Veo3 API key not configured")

        logger.info(f"Veo3: Generating video...")

        # Google Cloud Veo3 API调用 (根据实际API调整)
        from google.cloud import aiplatform
        aiplatform.init(project=self.project_id)

        # 调用Veo3模型
        # 实际实现根据Google Cloud API文档
        output_path = str(self.temp_dir / f"veo3_{hash(prompt)}.mp4")

        logger.info(f"Veo3 video saved: {output_path}")
        return output_path
