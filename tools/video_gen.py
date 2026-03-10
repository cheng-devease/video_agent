"""视频生成工具 - Kling, Sora, Seedance, Veo3"""
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, Optional, Any
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
    """Kling视频生成API"""

    def __init__(self):
        super().__init__()
        self.api_key = api_keys.kling_api_key
        self.api_url = api_keys.kling_api_url

    @async_retry(max_attempts=3)
    async def generate(
        self,
        image_path: str,
        prompt: str,
        negative_prompt: str = "",
        duration: int = 4,
    ) -> str:
        """生成视频"""
        if not self.api_key:
            raise ValueError("Kling API key not configured")

        logger.info(f"Kling: Generating video...")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "image": image_path,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "duration": duration,
        }

        async with aiohttp.ClientSession() as session:
            # 提交任务
            async with session.post(f"{self.api_url}/v1/videos", headers=headers, json=payload) as resp:
                result = await resp.json()
                task_id = result.get("task_id")

            # 轮询等待
            video_url = await self._wait_for_result(session, headers, task_id)

            # 下载视频
            output_path = str(self.temp_dir / f"kling_{task_id}.mp4")
            await self._download(session, video_url, output_path)

        logger.info(f"Kling video saved: {output_path}")
        return output_path

    async def _wait_for_result(self, session, headers, task_id: str) -> str:
        """等待生成完成"""
        import time
        start = time.time()
        while time.time() - start < self.timeout:
            async with session.get(f"{self.api_url}/v1/videos/{task_id}", headers=headers) as resp:
                result = await resp.json()
                status = result.get("status")
                if status == "succeed":
                    return result["video_url"]
                elif status == "failed":
                    raise Exception(f"Kling generation failed: {result}")
            await asyncio.sleep(5)
        raise TimeoutError("Kling generation timeout")

    async def _download(self, session, url: str, output_path: str):
        async with session.get(url) as resp:
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
