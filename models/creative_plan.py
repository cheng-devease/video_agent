"""创意方案数据模型"""
from dataclasses import dataclass, field
from typing import List, Optional
import json


@dataclass
class ScenePrompt:
    """场景提示词模型"""
    scene_id: int = 0
    scene_name: str = ""
    image_prompt: str = ""
    video_prompt_hint: str = ""
    duration: float = 4.0
    transition: str = "fade"


@dataclass
class CreativePlan:
    """创意方案模型"""

    # 广告风格
    ad_style: str = ""
    visual_style_reference: str = ""

    # 场景概念
    scene_concept: str = ""

    # 配色方案
    color_scheme: List[str] = field(default_factory=list)
    primary_color: str = ""
    secondary_color: str = ""

    # 情绪基调
    emotional_tone: str = ""

    # Hook策略
    hook_strategy: str = ""

    # 场景列表
    scenes: List[ScenePrompt] = field(default_factory=list)

    # 用户需求
    user_requirements: Optional[str] = None

    # 额外配置
    background_music_style: str = ""

    def to_dict(self) -> dict:
        return {
            "ad_style": self.ad_style,
            "visual_style_reference": self.visual_style_reference,
            "scene_concept": self.scene_concept,
            "color_scheme": self.color_scheme,
            "emotional_tone": self.emotional_tone,
            "hook_strategy": self.hook_strategy,
            "scenes": [
                {
                    "scene_id": s.scene_id,
                    "scene_name": s.scene_name,
                    "image_prompt": s.image_prompt,
                    "video_prompt_hint": s.video_prompt_hint,
                    "duration": s.duration,
                    "transition": s.transition,
                }
                for s in self.scenes
            ],
            "user_requirements": self.user_requirements,
            "background_music_style": self.background_music_style,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "CreativePlan":
        scenes = []
        for s in data.get("scenes", []):
            scenes.append(ScenePrompt(
                scene_id=s.get("scene_id", 0),
                scene_name=s.get("scene_name", ""),
                image_prompt=s.get("image_prompt", ""),
                video_prompt_hint=s.get("video_prompt_hint", ""),
                duration=s.get("duration", 4.0),
                transition=s.get("transition", "fade"),
            ))

        return cls(
            ad_style=data.get("ad_style", ""),
            visual_style_reference=data.get("visual_style_reference", ""),
            scene_concept=data.get("scene_concept", ""),
            color_scheme=data.get("color_scheme", []),
            emotional_tone=data.get("emotional_tone", ""),
            hook_strategy=data.get("hook_strategy", ""),
            scenes=scenes,
            user_requirements=data.get("user_requirements"),
            background_music_style=data.get("background_music_style", ""),
        )

    def get_total_duration(self) -> float:
        return sum(s.duration for s in self.scenes)
