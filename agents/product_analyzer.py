"""产品分析Agent"""
from typing import List
from agents.base import BaseAgent
from models.product_info import ProductInfo
from tools.llm import GPT4VisionTool
from config.prompts import prompts


class ProductAnalyzer(BaseAgent):
    """产品分析Agent - 分析产品图片，提取关键信息"""

    def __init__(self):
        super().__init__("ProductAnalyzer")
        self.vision_tool = GPT4VisionTool()

    async def execute(self, product_images: List[str]) -> ProductInfo:
        """
        分析产品图片

        Args:
            product_images: 产品图片路径列表

        Returns:
            ProductInfo: 产品信息对象
        """
        self.log_start(f"Analyzing {len(product_images)} product images")

        system_prompt, user_prompt = prompts.get_product_analyzer_prompts()

        try:
            result = await self.vision_tool.analyze_images_json(
                image_paths=product_images,
                prompt=user_prompt,
                system_prompt=system_prompt,
            )

            product_info = ProductInfo.from_dict(result)
            product_info.image_paths = product_images

            self.log_complete("Product analysis", product_info.get_summary())
            return product_info

        except Exception as e:
            self.log_error("Product analysis", e)
            raise
