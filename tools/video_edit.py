"""视频编辑工具 - 统一通过 fal.ai 调用"""
import asyncio
import base64
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from config.api_keys import api_keys
from config.settings import settings
from utils.logger import get_logger
from utils.retry import async_retry

logger = get_logger("video_edit")


class VideoEditTool:
    """视频编辑基础工具"""

    def __init__(self):
        self.output_dir = Path(settings.output_dir) / "edited_videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = settings.video_generation_timeout

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


class KlingVideoEditAPI(VideoEditTool):
    """Kling O3 Pro Video-to-Video Edit via fal.ai"""

    model_id = "fal-ai/kling-video/o3/pro/video-to-video/edit"
    queue_base_url = "https://queue.fal.run"

    def __init__(self):
        super().__init__()
        self.api_key = api_keys.fal_api_key

    @async_retry(max_attempts=3)
    async def edit(
        self,
        video_path: str,
        prompt: str,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not self.api_key:
            raise ValueError("FAL_API_KEY not configured for Kling video editing")
        if not prompt.strip():
            raise ValueError("Edit prompt is required for Kling video editing")

        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = self._build_payload(
            video_path=video_path,
            prompt=prompt,
            additional_params=additional_params,
        )

        async with aiohttp.ClientSession() as session:
            queue_info = await self._submit_request(session, headers, payload)
            result = await self._wait_for_result(session, headers, queue_info)
            video_url = self._extract_video_url(result)

            output_path = str(self.output_dir / f"kling_edit_{queue_info['request_id']}.mp4")
            await self._download(session, video_url, output_path)

        logger.info(f"Kling video edit saved: {output_path}")
        return output_path

    def _build_payload(
        self,
        video_path: str,
        prompt: str,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        params = dict(additional_params or {})
        payload: Dict[str, Any] = {
            "prompt": prompt,
            "video_url": self._normalize_media_input(params.pop("video_url", video_path)),
        }

        image_urls = params.pop("image_urls", [])
        if image_urls:
            payload["image_urls"] = [self._normalize_media_input(item) for item in image_urls]

        keep_audio = params.pop("keep_audio", None)
        if keep_audio is not None:
            payload["keep_audio"] = keep_audio

        shot_type = params.pop("shot_type", None)
        if shot_type:
            payload["shot_type"] = shot_type

        elements = params.pop("elements", [])
        if elements:
            payload["elements"] = self._normalize_elements(elements)

        for key, value in params.items():
            if value is not None:
                payload[key] = value

        return payload

    def _normalize_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for element in elements:
            item = dict(element)
            frontal = (
                item.pop("frontal_image_url", None)
                or item.pop("frontal_image", None)
                or item.pop("frontal_image_path", None)
            )
            refs = item.pop("reference_image_urls", None) or item.pop("reference_images", None) or []

            normalized_item = dict(item)
            if frontal is not None:
                normalized_item["frontal_image_url"] = self._normalize_media_input(frontal)
            if refs:
                normalized_item["reference_image_urls"] = [
                    self._normalize_media_input(ref)
                    for ref in refs
                ]
            normalized.append(normalized_item)
        return normalized

    async def _submit_request(self, session, headers, payload: Dict[str, Any]) -> Dict[str, str]:
        async with session.post(f"{self.queue_base_url}/{self.model_id}", headers=headers, json=payload) as resp:
            result = await resp.json()
            if resp.status >= 400:
                raise RuntimeError(f"Kling video edit submit failed: {result}")

        return self._resolve_queue_urls(result)

    def _resolve_queue_urls(self, submit_result: Dict[str, Any]) -> Dict[str, str]:
        request_id = submit_result.get("request_id")
        if not request_id:
            raise RuntimeError(f"Kling video edit submit missing request_id: {submit_result}")
        return {
            "request_id": request_id,
            "status_url": submit_result.get(
                "status_url",
                f"{self.queue_base_url}/{self.model_id}/requests/{request_id}/status",
            ),
            "response_url": submit_result.get(
                "response_url",
                f"{self.queue_base_url}/{self.model_id}/requests/{request_id}",
            ),
        }

    async def _wait_for_result(self, session, headers, queue_info: Dict[str, str]) -> Dict[str, Any]:
        import time

        start = time.time()
        while time.time() - start < self.timeout:
            async with session.get(queue_info["status_url"], headers=headers) as resp:
                result = await resp.json(content_type=None)
                status = result.get("status")
                if resp.status >= 400:
                    raise RuntimeError(f"Kling video edit status check failed: {result}")
                if status == "COMPLETED":
                    return await self._get_result(session, headers, queue_info["response_url"])
                if status in {"FAILED", "ERROR", "CANCELLED"}:
                    raise RuntimeError(f"Kling video edit failed: {result}")
            await asyncio.sleep(5)
        raise TimeoutError("Kling video edit timeout")

    async def _get_result(self, session, headers, response_url: str) -> Dict[str, Any]:
        async with session.get(response_url, headers=headers) as resp:
            result = await resp.json(content_type=None)
            if resp.status >= 400:
                raise RuntimeError(f"Kling video edit result fetch failed: {result}")
        return result

    def _extract_video_url(self, result: Dict[str, Any]) -> str:
        response = result.get("response", result)
        if isinstance(response, dict):
            if isinstance(response.get("video"), dict) and response["video"].get("url"):
                return response["video"]["url"]
            if response.get("video_url"):
                return response["video_url"]
        raise RuntimeError(f"Kling video edit result missing video URL: {result}")

    async def _download(self, session, url: str, output_path: str):
        async with session.get(url) as resp:
            if resp.status >= 400:
                raise RuntimeError(f"Failed to download edited video: {url}")
            with open(output_path, "wb") as f:
                f.write(await resp.read())


class MoviePyEditor(VideoEditTool):
    """保留给 BrandComposer 的本地基础编辑工具"""

    def __init__(self):
        super().__init__()
        from moviepy.editor import AudioFileClip, CompositeVideoClip, ImageClip, TextClip, VideoFileClip

        self.VideoFileClip = VideoFileClip
        self.CompositeVideoClip = CompositeVideoClip
        self.ImageClip = ImageClip
        self.TextClip = TextClip
        self.AudioFileClip = AudioFileClip

    def add_logo(
        self,
        video_path: str,
        logo_path: str,
        position=("right", "top"),
        logo_height: int = 50,
        output_path: Optional[str] = None,
    ) -> str:
        video = self.VideoFileClip(video_path)
        logo = (
            self.ImageClip(logo_path)
            .set_duration(video.duration)
            .resize(height=logo_height)
            .set_position(position)
        )
        final = self.CompositeVideoClip([video, logo])

        if not output_path:
            output_path = str(self.output_dir / f"branded_{Path(video_path).stem}.mp4")

        final.write_videofile(output_path, codec="libx264", audio_codec="aac")
        final.close()
        return output_path

    def add_text(
        self,
        video_path: str,
        text: str,
        position=("center", "bottom"),
        fontsize: int = 30,
        color: str = "white",
        font: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> str:
        video = self.VideoFileClip(video_path)
        txt_clip = (
            self.TextClip(text, fontsize=fontsize, color=color, font=font)
            .set_duration(video.duration)
            .set_position(position)
        )
        final = self.CompositeVideoClip([video, txt_clip])

        if not output_path:
            output_path = str(self.output_dir / f"text_{Path(video_path).stem}.mp4")

        final.write_videofile(output_path, codec="libx264", audio_codec="aac")
        final.close()
        return output_path

    def add_audio(
        self,
        video_path: str,
        audio_path: str,
        volume: float = 0.3,
        output_path: Optional[str] = None,
    ) -> str:
        video = self.VideoFileClip(video_path)
        audio = self.AudioFileClip(audio_path).volumex(volume)

        if audio.duration < video.duration:
            audio = audio.loop(duration=video.duration)
        else:
            audio = audio.subclip(0, video.duration)

        final = video.set_audio(audio)

        if not output_path:
            output_path = str(self.output_dir / f"audio_{Path(video_path).stem}.mp4")

        final.write_videofile(output_path, codec="libx264", audio_codec="aac")
        final.close()
        return output_path
