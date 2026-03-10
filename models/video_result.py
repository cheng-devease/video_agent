"""视频结果数据模型"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import json


@dataclass
class VideoPrompt:
    """视频生成Prompt"""
    model_name: str
    prompt: str
    negative_prompt: str = ""
    additional_params: Dict = field(default_factory=dict)


@dataclass
class VideoResult:
    """视频生成结果"""
    model_name: str
    video_path: str
    prompt_used: str = ""
    duration: float = 0.0
    resolution: str = ""
    file_size: int = 0
    generation_time: float = 0.0
    success: bool = True
    error_message: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "video_path": self.video_path,
            "prompt_used": self.prompt_used,
            "duration": self.duration,
            "resolution": self.resolution,
            "file_size": self.file_size,
            "generation_time": self.generation_time,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class EvaluationScore:
    """评估分数"""
    product_consistency: float = 0.0  # 产品一致性 (0-25)
    visual_quality: float = 0.0  # 视觉质量 (0-25)
    creativity: float = 0.0  # 创意契合度 (0-25)
    ad_effectiveness: float = 0.0  # 广告效果 (0-25)

    @property
    def total_score(self) -> float:
        return (
            self.product_consistency
            + self.visual_quality
            + self.creativity
            + self.ad_effectiveness
        )

    def to_dict(self) -> dict:
        return {
            "product_consistency": self.product_consistency,
            "visual_quality": self.visual_quality,
            "creativity": self.creativity,
            "ad_effectiveness": self.ad_effectiveness,
            "total_score": self.total_score,
        }


@dataclass
class EvaluationResult:
    """质量评估结果"""
    model_name: str
    video_path: str
    score: EvaluationScore
    ranking: int = 0
    comments: str = ""
    is_best: bool = False
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "video_path": self.video_path,
            "score": self.score.to_dict(),
            "ranking": self.ranking,
            "comments": self.comments,
            "is_best": self.is_best,
            "metadata": self.metadata,
        }


@dataclass
class VideoGenerationResult:
    """完整的视频生成结果"""
    # 所有生成的视频
    all_videos: List[VideoResult] = field(default_factory=list)

    # 所有评估结果
    evaluations: List[EvaluationResult] = field(default_factory=list)

    # 最佳视频
    best_video: Optional[VideoResult] = None
    best_evaluation: Optional[EvaluationResult] = None

    # 最终输出视频
    final_video_path: str = ""

    def to_dict(self) -> dict:
        return {
            "all_videos": [v.to_dict() for v in self.all_videos],
            "evaluations": [e.to_dict() for e in self.evaluations],
            "best_video": self.best_video.to_dict() if self.best_video else None,
            "best_evaluation": self.best_evaluation.to_dict() if self.best_evaluation else None,
            "final_video_path": self.final_video_path,
        }

    def get_successful_videos(self) -> List[VideoResult]:
        return [v for v in self.all_videos if v.success]

    def get_best_video_path(self) -> str:
        if self.best_video:
            return self.best_video.video_path
        successful = self.get_successful_videos()
        return successful[0].video_path if successful else ""
