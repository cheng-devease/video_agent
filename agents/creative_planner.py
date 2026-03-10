"""创意策划Agent"""
from typing import Optional
from agents.base import BaseAgent
from models.product_info import ProductInfo
from models.creative_plan import CreativePlan, ScenePrompt
from tools.llm import LLMTool
from config.prompts import prompts


class CreativePlanner(BaseAgent):
    """创意策划Agent - 设计广告创意方案"""

    def __init__(self):
        super().__init__("CreativePlanner")
        self.llm_tool = LLMTool()

    async def execute(
        self,
        product_info: ProductInfo,
        user_requirements: Optional[str] = None,
    ) -> CreativePlan:
        """
        设计广告创意方案

        Args:
            product_info: 产品信息
            user_requirements: 用户额外需求

        Returns:
            CreativePlan: 创意方案
        """
        self.log_start("Creating creative plan")

        system_prompt, user_prompt_template = prompts.get_creative_planner_prompts()

        user_prompt = user_prompt_template.format(
            product_info=product_info.to_json(),
            user_requirements=user_requirements or "无特殊要求",
        )

        try:
            result = await self.llm_tool.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
            )

            creative_plan = CreativePlan.from_dict(result)
            creative_plan.user_requirements = user_requirements

            self.log_complete(
                "Creative planning",
                f"Style: {creative_plan.ad_style}, Scenes: {creative_plan.get_total_duration()}s",
            )
            return creative_plan

        except Exception as e:
            self.log_error("Creative planning", e)
            raise
