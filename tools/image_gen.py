"""图像生成工具 - FLUX等"""
import aiohttp
import base64
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional
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

    def _normalize_image_input(self, image_input: Any) -> str:
        if image_input is None:
            raise ValueError("Image input cannot be empty")

        image_str = str(image_input)
        if image_str.startswith(("http://", "https://", "data:")):
            return image_str

        path = Path(image_str)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_str}")

        mime_type, _ = mimetypes.guess_type(path.name)
        mime_type = mime_type or "application/octet-stream"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"


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


class NanoBananaEditTool(ImageGenTool):
    """Nano Banana 2 image edit tool via fal.ai"""

    model_id = "fal-ai/nano-banana-2/edit"
    endpoint = "https://fal.run/fal-ai/nano-banana-2/edit"

    def __init__(self):
        super().__init__()
        self.api_key = api_keys.fal_api_key

    @async_retry(max_attempts=3)
    async def edit(
        self,
        prompt: str,
        image_paths: List[str],
        additional_params: Optional[Dict[str, Any]] = None,
        output_path: Optional[str] = None,
    ) -> str:
        if not self.api_key:
            raise ValueError("FAL_API_KEY not configured for Nano Banana scene generation")
        if not prompt.strip():
            raise ValueError("Prompt is required for Nano Banana scene generation")
        if not image_paths:
            raise ValueError("At least one image is required for Nano Banana scene generation")

        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = self._build_payload(
            prompt=prompt,
            image_paths=image_paths,
            additional_params=additional_params,
        )

        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, headers=headers, json=payload) as resp:
                result = await resp.json(content_type=None)
                if resp.status >= 400:
                    raise RuntimeError(f"Nano Banana edit failed: {result}")

            image_url = self._extract_image_url(result)

            if not output_path:
                import time
                output_path = str(self.temp_dir / f"scene_{int(time.time())}.png")

            async with session.get(image_url) as resp:
                if resp.status >= 400:
                    raise RuntimeError(f"Failed to download Nano Banana image: {image_url}")
                with open(output_path, "wb") as f:
                    f.write(await resp.read())

        logger.info(f"Nano Banana image saved: {output_path}")
        return output_path

    def _build_payload(
        self,
        prompt: str,
        image_paths: List[str],
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "prompt": prompt,
            "image_urls": [self._normalize_image_input(image_path) for image_path in image_paths],
        }

        for key, value in dict(additional_params or {}).items():
            if value is not None:
                payload[key] = value

        return payload

    def _extract_image_url(self, result: Dict[str, Any]) -> str:
        images = result.get("images")
        if isinstance(images, list) and images:
            first_image = images[0]
            if isinstance(first_image, dict) and first_image.get("url"):
                return first_image["url"]

        image = result.get("image")
        if isinstance(image, dict) and image.get("url"):
            return image["url"]

        raise RuntimeError(f"Nano Banana result missing image URL: {result}")
