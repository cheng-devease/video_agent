"""图像生成工具 - FLUX等"""
import aiohttp
from pathlib import Path
from typing import Optional
from config.api_keys import api_keys
from config.settings import settings
from utils.logger import get_logger
from utils.retry import async_retry

logger = get_logger("image_gen")


class ImageGenTool:
    """图像生成基础工具"""

    def __init__(self):
        self.temp_dir = Path(settings.temp_dir) / "images"
        self.temp_dir.mkdir(parents=True, exist_ok=True)


class FLUXTool(ImageGenTool):
    """FLUX图像生成工具"""

    def __init__(self):
        super().__init__()
        self.api_key = api_keys.flux_api_key
        self.api_url = api_keys.flux_api_url

    @async_retry(max_attempts=3)
    async def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1920,
        height: int = 1080,
        output_path: Optional[str] = None,
    ) -> str:
        """生成图像"""
        if not self.api_key:
            raise ValueError("FLUX API key not configured")

        logger.info(f"Generating image: {prompt[:50]}...")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {"prompt": prompt, "width": width, "height": height}
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    raise Exception(f"FLUX API error: {await resp.text()}")
                result = await resp.json()

        image_url = result.get("images", [{}])[0].get("url")
        if not image_url:
            raise Exception("No image URL in response")

        if not output_path:
            import time
            output_path = str(self.temp_dir / f"scene_{int(time.time())}.png")

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                with open(output_path, "wb") as f:
                    f.write(await resp.read())

        logger.info(f"Image saved: {output_path}")
        return output_path
