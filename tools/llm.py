"""LLM调用工具 - 支持GPT-4V视觉分析"""
import base64
from pathlib import Path
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from config.api_keys import api_keys
from config.settings import settings
from utils.logger import get_logger
from utils.retry import async_retry

logger = get_logger("llm")


class LLMTool:
    """LLM基础工具"""

    def __init__(self):
        self.api_key = api_keys.openai_api_key
        self.base_url = api_keys.openai_base_url
        self.model = settings.primary_llm
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    @async_retry(max_attempts=3)
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """生成文本"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    @async_retry(max_attempts=3)
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """生成JSON响应"""
        import json
        response = await self.generate(prompt=prompt, system_prompt=system_prompt)

        # 提取JSON
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start != -1:
            return json.loads(response[json_start:json_end])
        return json.loads(response)


class GPT4VisionTool(LLMTool):
    """GPT-4V视觉分析工具"""

    def __init__(self):
        super().__init__()
        self.model = "gpt-4o"

    def _encode_image(self, image_path: str) -> str:
        """编码图片为base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    @async_retry(max_attempts=3)
    async def analyze_images(
        self,
        image_paths: List[str],
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """分析图片"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        content = [{"type": "text", "text": prompt}]
        for path in image_paths:
            if Path(path).exists():
                b64 = self._encode_image(path)
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })

        messages.append({"role": "user", "content": content})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096,
        )
        return response.choices[0].message.content

    @async_retry(max_attempts=3)
    async def analyze_images_json(
        self,
        image_paths: List[str],
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """分析图片并返回JSON"""
        import json
        response = await self.analyze_images(image_paths, prompt, system_prompt)
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        return json.loads(response[json_start:json_end])
