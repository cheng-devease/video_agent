"""场景生成Agent"""
from pathlib import Path
from typing import List
from agents.base import BaseAgent
from models.creative_plan import CreativePlan
from models.product_info import ProductInfo
from tools.image_gen import NanoBananaEditTool
from config.settings import settings


class SceneGenerator(BaseAgent):
    """场景生成Agent - 生成广告场景图片"""

    system_prompt_path = Path(__file__).resolve().parents[1] / "system_prompt_image_gen.md"

    def __init__(self):
        super().__init__("SceneGenerator")
        self.image_tool = NanoBananaEditTool()
        self.system_prompt = self.system_prompt_path.read_text(encoding="utf-8")

    async def execute(
        self,
        creative_plan: CreativePlan,
        product_images: List[str],
        product_info: ProductInfo,
        compose_product: bool = False,
    ) -> List[str]:
        """
        生成场景图片

        Args:
            creative_plan: 创意方案
            product_images: 产品图片路径
            product_info: 产品信息
            compose_product: 是否将产品合成到场景中

        Returns:
            List[str]: 场景图片路径列表
        """
        self.log_start(f"Generating {len(creative_plan.scenes)} scenes")

        scene_images = []

        for i, scene in enumerate(creative_plan.scenes):
            try:
                self.logger.info(f"Generating scene {i + 1}: {scene.scene_name}")

                scene_image = await self.image_tool.edit(
                    prompt=self._build_edit_prompt(creative_plan, scene, product_info),
                    image_paths=product_images,
                    additional_params=self._build_edit_params(),
                )

                scene_images.append(scene_image)

            except Exception as e:
                self.log_error(f"Scene {i + 1} generation", e)
                # 继续生成其他场景
                continue

        self.log_complete("Scene generation", f"Generated {len(scene_images)} scenes")
        return scene_images

    def _build_edit_prompt(
        self,
        creative_plan: CreativePlan,
        scene,
        product_info: ProductInfo,
    ) -> str:
        sections = []
        if self.system_prompt.strip():
            sections.append(self.system_prompt.strip())

        sections.append(
            "Create a polished advertising first frame using all provided product reference images. "
            "Preserve product identity, geometry, material, color, logo, and signature details."
        )
        sections.append(f"Creative plan style: {creative_plan.ad_style}")
        sections.append(f"Creative plan tone: {creative_plan.emotional_tone}")
        sections.append(f"Hook strategy: {creative_plan.hook_strategy}")
        sections.append(f"Scene name: {scene.scene_name}")
        sections.append(f"Scene image direction: {scene.image_prompt}")

        if scene.video_prompt_hint:
            sections.append(f"Video framing hint: {scene.video_prompt_hint}")

        sections.append(f"Product information JSON:\n{product_info.to_json()}")
        return "\n\n".join(section for section in sections if section.strip())

    def _build_edit_params(self):
        return {
            "num_images": 1,
            "aspect_ratio": settings.video_aspect_ratio.value,
            "output_format": "png",
            "resolution": "1K",
            "limit_generations": True,
            "enable_web_search": False,
        }
