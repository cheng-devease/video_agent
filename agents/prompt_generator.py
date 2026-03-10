"""Prompt生成Agent"""
from pathlib import Path
from typing import Dict, Any
from agents.base import BaseAgent
from models.creative_plan import CreativePlan
from tools.llm import GPT4VisionTool


class PromptGenerator(BaseAgent):
    """Prompt生成Agent - 为各视频模型生成专用Prompt"""

    system_prompt_path = Path(__file__).resolve().parents[1] / "system_prompt_video_gen.md"

    def __init__(self):
        super().__init__("PromptGenerator")
        self.vision_tool = GPT4VisionTool()
        self.system_prompt = self.system_prompt_path.read_text(encoding="utf-8")

    async def execute(
        self,
        scene_image: str,
        product_image: str,
        creative_plan: CreativePlan,
    ) -> Dict[str, Any]:
        """
        生成各模型的视频Prompt

        Args:
            scene_image: 场景图片路径
            product_image: 产品图片路径
            creative_plan: 创意方案

        Returns:
            Dict: 各模型的Prompt配置
        """
        self.log_start("Generating video prompts")

        full_prompt = self._build_user_prompt(creative_plan)

        try:
            raw_result = await self.vision_tool.analyze_images_json(
                image_paths=[scene_image, product_image],
                prompt=full_prompt,
                system_prompt=self.system_prompt,
            )
            result = self._normalize_result(raw_result)

            # 确保包含所有模型
            required_models = ["kling", "sora2", "seedance", "veo3"]
            for model in required_models:
                if model not in result:
                    result[model] = {"prompt": "", "additional_params": {}}

            self.log_complete("Prompt generation", f"Generated prompts for {len(result)} models")
            return result

        except Exception as e:
            self.log_error("Prompt generation", e)
            # 返回默认结构
            return {
                "kling": {"prompt": "", "negative_prompt": "", "additional_params": {}},
                "sora2": {"prompt": "", "additional_params": {}},
                "seedance": {"prompt": "", "additional_params": {}},
                "veo3": {"prompt": "", "additional_params": {}},
            }

    def _build_user_prompt(self, creative_plan: CreativePlan) -> str:
        return f"""
请严格基于你收到的两张图片和以下创意约束，输出单个 JSON 对象，不要输出 Markdown，不要输出额外解释。

创意方案信息:
- 广告风格: {creative_plan.ad_style}
- 视觉参考: {creative_plan.visual_style_reference}
- 场景概念: {creative_plan.scene_concept}
- 情绪基调: {creative_plan.emotional_tone}
- Hook策略: {creative_plan.hook_strategy}
- 用户需求: {creative_plan.user_requirements or ""}

请返回 `model_prompts`，并为以下 4 个模型分别生成可直接用于视频生成的字段：
- kling -> fal-ai/kling-video/v3/pro/image-to-video
- sora2 -> fal-ai/sora-2/image-to-video
- seedance -> fal-ai/bytedance/seedance/v1.5/pro/image-to-video
- veo3 -> fal-ai/veo3.1/image-to-video

每个模型都必须包含 `generation_params`。
除非图片内容强烈要求，否则默认：
- duration 使用 "5"
- aspect_ratio 与输入首帧主构图一致
- 只保留一个核心卖点
- 提示词使用英文
"""

    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        model_prompts = result.get("model_prompts", result)
        return {
            "kling": self._normalize_kling(model_prompts.get("kling", {})),
            "sora2": self._normalize_sora(model_prompts.get("sora2", {})),
            "seedance": self._normalize_seedance(model_prompts.get("seedance", {})),
            "veo3": self._normalize_veo(model_prompts.get("veo3", {})),
        }

    def _normalize_kling(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "prompt": self._stringify_sections(data.get("prompt")),
            "negative_prompt": data.get("negative_prompt", ""),
            "additional_params": dict(data.get("generation_params", {})),
        }

    def _normalize_sora(self, data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._stringify_sections(data.get("prompt"))
        dialogue_block = data.get("dialogue_block")
        audio_description = data.get("audio_description")
        parts = [prompt]
        if dialogue_block:
            parts.append(f"Dialogue:\n{dialogue_block}")
        if audio_description:
            parts.append(f"Audio: {audio_description}")
        return {
            "prompt": "\n".join(part for part in parts if part),
            "additional_params": dict(data.get("generation_params", {})),
        }

    def _normalize_seedance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "prompt": self._stringify_sections(data.get("prompt"), separator=". "),
            "additional_params": dict(data.get("generation_params", {})),
        }

    def _normalize_veo(self, data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = data.get("full_prompt") or self._stringify_sections(data.get("prompt"), separator=". ")
        return {
            "prompt": prompt,
            "additional_params": dict(data.get("generation_params", {})),
        }

    def _stringify_sections(self, value: Any, separator: str = ", ") -> str:
        if isinstance(value, dict):
            return separator.join(str(item).strip() for item in value.values() if str(item).strip())
        if isinstance(value, list):
            return separator.join(str(item).strip() for item in value if str(item).strip())
        return str(value or "").strip()
