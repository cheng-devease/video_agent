"""场景生成Agent"""
from typing import List
from agents.base import BaseAgent
from models.creative_plan import CreativePlan
from tools.image_gen import FLUXTool
from tools.image_process import ImageComposeTool, RemoveBGTool
from config.settings import settings
from utils.logger import get_logger


class SceneGenerator(BaseAgent):
    """场景生成Agent - 生成广告场景图片"""

    def __init__(self):
        super().__init__("SceneGenerator")
        self.flux_tool = FLUXTool()
        self.compose_tool = ImageComposeTool()
        self.remove_bg_tool = RemoveBGTool()

    async def execute(
        self,
        creative_plan: CreativePlan,
        product_images: List[str],
        compose_product: bool = False,
    ) -> List[str]:
        """
        生成场景图片

        Args:
            creative_plan: 创意方案
            product_images: 产品图片路径
            compose_product: 是否将产品合成到场景中

        Returns:
            List[str]: 场景图片路径列表
        """
        self.log_start(f"Generating {len(creative_plan.scenes)} scenes")

        scene_images = []

        for i, scene in enumerate(creative_plan.scenes):
            try:
                self.logger.info(f"Generating scene {i + 1}: {scene.scene_name}")

                # 生成场景背景
                scene_image = await self.flux_tool.generate(
                    prompt=scene.image_prompt,
                    width=settings.image_width,
                    height=settings.image_height,
                )

                # 可选：合成产品到场景
                if compose_product and product_images:
                    product_cutout = self.remove_bg_tool.remove_background(product_images[0])
                    scene_image = self.compose_tool.compose(
                        background_path=scene_image,
                        foreground_path=product_cutout,
                        position=self._calculate_position(scene_image),
                    )

                scene_images.append(scene_image)

            except Exception as e:
                self.log_error(f"Scene {i + 1} generation", e)
                # 继续生成其他场景
                continue

        self.log_complete("Scene generation", f"Generated {len(scene_images)} scenes")
        return scene_images

    def _calculate_position(self, background_path: str):
        """计算产品在场景中的位置（居中偏下）"""
        from PIL import Image

        bg = Image.open(background_path)
        # 返回居中位置
        return (bg.width // 4, bg.height // 3)
