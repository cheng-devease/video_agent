"""品牌合成Agent"""
from typing import Optional
from dataclasses import dataclass
from agents.base import BaseAgent
from tools.video_edit import MoviePyEditor
from config.settings import settings


@dataclass
class BrandAssets:
    """品牌素材"""
    logo_path: Optional[str] = None
    logo_position: str = "top-right"
    logo_height: int = 50

    cta_text: Optional[str] = None
    cta_position: str = "bottom-center"
    cta_fontsize: int = 30
    cta_color: str = "white"

    background_music: Optional[str] = None
    music_volume: float = 0.3

    brand_name: Optional[str] = None
    primary_color: str = "#FFFFFF"


class BrandComposer(BaseAgent):
    """品牌合成Agent - 添加品牌元素到视频"""

    def __init__(self):
        super().__init__("BrandComposer")
        self.editor = MoviePyEditor()

    async def execute(
        self,
        video_path: str,
        brand_assets: Optional[BrandAssets] = None,
    ) -> str:
        """
        添加品牌元素

        Args:
            video_path: 视频路径
            brand_assets: 品牌素材

        Returns:
            str: 成品视频路径
        """
        self.log_start("Adding brand elements")

        brand_assets = brand_assets or BrandAssets()

        current_path = video_path

        try:
            # 添加Logo
            if brand_assets.logo_path:
                position_map = {
                    "top-left": ("left", "top"),
                    "top-right": ("right", "top"),
                    "bottom-left": ("left", "bottom"),
                    "bottom-right": ("right", "bottom"),
                }
                position = position_map.get(brand_assets.logo_position, ("right", "top"))

                current_path = self.editor.add_logo(
                    video_path=current_path,
                    logo_path=brand_assets.logo_path,
                    position=position,
                    logo_height=brand_assets.logo_height,
                )

            # 添加CTA文字
            if brand_assets.cta_text:
                position_map = {
                    "top-center": ("center", "top"),
                    "bottom-center": ("center", "bottom"),
                    "center": ("center", "center"),
                }
                position = position_map.get(brand_assets.cta_position, ("center", "bottom"))

                current_path = self.editor.add_text(
                    video_path=current_path,
                    text=brand_assets.cta_text,
                    position=position,
                    fontsize=brand_assets.cta_fontsize,
                    color=brand_assets.cta_color,
                )

            # 添加背景音乐
            if brand_assets.background_music:
                current_path = self.editor.add_audio(
                    video_path=current_path,
                    audio_path=brand_assets.background_music,
                    volume=brand_assets.music_volume,
                )

            self.log_complete("Brand composition", current_path)
            return current_path

        except Exception as e:
            self.log_error("Brand composition", e)
            # 返回原始视频
            return video_path
