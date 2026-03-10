"""视频编辑Agent"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent
from models.video_result import VideoResult
from tools.video_edit import KlingVideoEditAPI


@dataclass
class EditConfig:
    """AI 视频编辑配置"""

    prompt: str = ""
    image_urls: List[str] = field(default_factory=list)
    keep_audio: bool = True
    shot_type: str = "customize"
    elements: List[Dict[str, Any]] = field(default_factory=list)
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def to_additional_params(self) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "image_urls": list(self.image_urls),
            "keep_audio": self.keep_audio,
            "shot_type": self.shot_type,
            "elements": list(self.elements),
        }
        for key, value in self.extra_params.items():
            if value is not None:
                params[key] = value
        return params


class VideoEditor(BaseAgent):
    """视频编辑Agent - 使用 AI 模型对视频进行编辑"""

    def __init__(self):
        super().__init__("VideoEditor")
        self.editor = KlingVideoEditAPI()

    async def execute(
        self,
        video: VideoResult,
        config: Optional[EditConfig] = None,
    ) -> str:
        self.log_start(f"Editing video from {video.model_name}")

        if not video.success or not video.video_path:
            raise ValueError("Cannot edit failed video")

        config = config or EditConfig()

        try:
            edited_path = await self.edit_video(
                video_path=video.video_path,
                prompt=config.prompt,
                additional_params=config.to_additional_params(),
                source_prompt=video.prompt_used,
            )
            self.log_complete("Video editing", edited_path)
            return edited_path
        except Exception as e:
            self.log_error("Video editing", e)
            return video.video_path

    async def edit_video(
        self,
        video_path: str,
        prompt: str = "",
        additional_params: Optional[Dict[str, Any]] = None,
        source_prompt: str = "",
    ) -> str:
        effective_prompt = prompt.strip() or self._build_default_prompt(source_prompt)
        return await self.editor.edit(
            video_path=video_path,
            prompt=effective_prompt,
            additional_params=additional_params or {},
        )

    def _build_default_prompt(self, source_prompt: str) -> str:
        base_instruction = (
            "Refine @Video1 into a stronger premium product ad edit while preserving product identity, "
            "physical realism, shot continuity, and the main commercial message."
        )
        if source_prompt:
            return f"{base_instruction} Preserve the core intent of this original prompt: {source_prompt}"
        return base_instruction
