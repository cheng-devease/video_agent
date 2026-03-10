"""Prompt生成Agent"""
from typing import Dict, Any
from agents.base import BaseAgent
from models.creative_plan import CreativePlan
from tools.llm import GPT4VisionTool
from config.prompts import prompts


class PromptGenerator(BaseAgent):
    """Prompt生成Agent - 为各视频模型生成专用Prompt"""

    def __init__(self):
        super().__init__("PromptGenerator")
        self.vision_tool = GPT4VisionTool()

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

        system_prompt, user_prompt = prompts.get_prompt_generator_prompts()

        # 构建完整的prompt
        full_prompt = f"""
{user_prompt}

创意方案信息:
- 广告风格: {creative_plan.ad_style}
- 情绪基调: {creative_plan.emotional_tone}
- Hook策略: {creative_plan.hook_strategy}

请为以下图片生成4秒产品广告视频的Prompt。
"""

        try:
            result = await self.vision_tool.analyze_images_json(
                image_paths=[scene_image, product_image],
                prompt=full_prompt,
                system_prompt=system_prompt,
            )

            # 确保包含所有模型
            required_models = ["kling", "sora2", "seedance", "veo3"]
            for model in required_models:
                if model not in result:
                    result[model] = {"prompt": ""}

            self.log_complete("Prompt generation", f"Generated prompts for {len(result)} models")
            return result

        except Exception as e:
            self.log_error("Prompt generation", e)
            # 返回默认结构
            return {
                "kling": {"prompt": "", "negative_prompt": ""},
                "sora2": {"prompt": ""},
                "seedance": {"full_prompt": ""},
                "veo3": {"prompt": ""},
            }
