"""全局配置"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class VideoQuality(Enum):
    """视频质量等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


class AspectRatio(Enum):
    """视频宽高比"""
    RATIO_16_9 = "16:9"
    RATIO_9_16 = "9:16"
    RATIO_1_1 = "1:1"
    RATIO_4_3 = "4:3"


@dataclass
class Settings:
    """全局配置类"""

    # 视频生成配置
    video_duration_min: int = 4
    video_duration_max: int = 15
    video_default_duration: int = 4
    video_generation_timeout: int = 600
    video_quality: VideoQuality = VideoQuality.HIGH
    video_aspect_ratio: AspectRatio = AspectRatio.RATIO_16_9
    video_fps: int = 30

    # 图像生成配置
    image_width: int = 1920
    image_height: int = 1080
    image_quality: str = "high"

    # 工作流配置
    max_concurrent_tasks: int = 4
    task_timeout: int = 300  # 秒
    enable_parallel_video_gen: bool = True

    # 上下文管理配置
    context_window_threshold: float = 0.6  # 60%时触发压缩
    max_context_tokens: int = 128000  # GPT-4 Turbo上下文窗口

    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 3600  # 秒
    cache_dir: str = "./cache"

    # 输出配置
    output_dir: str = "./output"
    temp_dir: str = "./temp"

    # 日志配置
    log_level: str = "INFO"
    log_file: str = "./logs/video_agent.log"

    # 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_exponential_base: float = 2.0

    # 模型选择
    primary_llm: str = "gpt-4-vision-preview"
    fallback_llm: str = "gpt-4-turbo"

    # 视频生成模型优先级
    video_models_priority: List[str] = field(
        default_factory=lambda: ["kling", "seedance", "veo3", "sora2"]
    )

    # 品牌合成配置
    default_logo_position: str = "top-right"
    default_cta_position: str = "bottom-center"
    default_music_volume: float = 0.3


# 全局配置实例
settings = Settings()
