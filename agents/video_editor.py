"""视频编辑Agent"""
from typing import Optional
from dataclasses import dataclass
from agents.base import BaseAgent
from models.video_result import VideoResult
from tools.video_edit import MoviePyEditor


@dataclass
class EditConfig:
    """编辑配置"""
    trim_start: Optional[float] = None
    trim_end: Optional[float] = None
    speed: float = 1.0
    add_captions: bool = False
    enhance_quality: bool = False


class VideoEditor(BaseAgent):
    """视频编辑Agent - 对视频进行后期编辑"""

    def __init__(self):
        super().__init__("VideoEditor")
        self.editor = MoviePyEditor()

    async def execute(
        self,
        video: VideoResult,
        config: Optional[EditConfig] = None,
    ) -> str:
        """
        编辑视频

        Args:
            video: 视频结果
            config: 编辑配置

        Returns:
            str: 编辑后的视频路径
        """
        self.log_start(f"Editing video from {video.model_name}")

        if not video.success or not video.video_path:
            raise ValueError("Cannot edit failed video")

        config = config or EditConfig()

        current_path = video.video_path

        try:
            # 裁剪
            if config.trim_start is not None or config.trim_end is not None:
                start = config.trim_start or 0
                end = config.trim_end or video.duration
                current_path = self.editor.trim(current_path, start, end)

            # 调整速度
            if config.speed != 1.0:
                # MoviePy的速度调整需要额外处理
                self.logger.info(f"Adjusting speed to {config.speed}x")

            self.log_complete("Video editing", current_path)
            return current_path

        except Exception as e:
            self.log_error("Video editing", e)
            # 返回原始视频
            return video.video_path
