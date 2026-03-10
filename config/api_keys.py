"""API密钥配置 - 用户需要填写这些密钥"""
from dataclasses import dataclass
import os
from typing import Optional


@dataclass
class APIKeys:
    """API密钥配置类"""

    # ==================== LLM API密钥 ====================
    openai_api_key: str = ""  # OpenAI API密钥 (必需)
    openai_base_url: Optional[str] = None  # OpenAI API基础URL (可选，用于代理)
    anthropic_api_key: str = ""  # Anthropic API密钥 (可选)

    # ==================== 图像生成API密钥 ====================
    flux_api_key: str = ""  # FLUX API密钥
    flux_api_url: str = ""  # FLUX API URL (如: fal.ai / Replicate)
    replicate_api_token: str = ""  # Replicate API Token (可选)

    # ==================== 视频生成API密钥 ====================
    # fal.ai API (推荐，支持多种视频模型)
    fal_api_key: str = ""  # fal.ai API密钥

    # Kling API (如果直接使用可灵官方API)
    kling_api_key: str = ""  # Kling API密钥
    kling_api_url: str = ""  # Kling API URL

    sora_api_key: str = ""  # OpenAI Sora API密钥 (通常与openai_api_key相同)

    seedance_api_key: str = ""  # Seedance/即梦 API密钥
    seedance_api_url: str = ""  # Seedance API URL

    veo3_api_key: str = ""  # Google Veo3 API密钥
    veo3_project_id: str = ""  # Google Cloud项目ID

    # ==================== 视频编辑API密钥 ====================
    opusclip_api_key: str = ""  # OpusClip API密钥 (可选)

    # ==================== 云存储API密钥 ====================
    aws_access_key: str = ""  # AWS Access Key (可选)
    aws_secret_key: str = ""  # AWS Secret Key (可选)
    aws_region: str = ""  # AWS Region (可选)
    s3_bucket: str = ""  # S3 Bucket名称 (可选)

    google_cloud_credentials: str = ""  # Google Cloud凭据文件路径 (可选)

    def load_from_env(self):
        """从环境变量加载API密钥"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")

        self.flux_api_key = os.getenv("FLUX_API_KEY", "")
        self.flux_api_url = os.getenv("FLUX_API_URL", "")
        self.replicate_api_token = os.getenv("REPLICATE_API_TOKEN", "")

        # fal.ai API
        self.fal_api_key = os.getenv("FAL_API_KEY", "")

        self.kling_api_key = os.getenv("KLING_API_KEY", "")
        self.kling_api_url = os.getenv("KLING_API_URL", "")

        self.sora_api_key = os.getenv("SORA_API_KEY", "") or self.openai_api_key

        self.seedance_api_key = os.getenv("SEEDANCE_API_KEY", "")
        self.seedance_api_url = os.getenv("SEEDANCE_API_URL", "")

        self.veo3_api_key = os.getenv("VEO3_API_KEY", "")
        self.veo3_project_id = os.getenv("VEO3_PROJECT_ID", "")

        self.opusclip_api_key = os.getenv("OPUSCLIP_API_KEY", "")

        self.aws_access_key = os.getenv("AWS_ACCESS_KEY", "")
        self.aws_secret_key = os.getenv("AWS_SECRET_KEY", "")
        self.aws_region = os.getenv("AWS_REGION", "")
        self.s3_bucket = os.getenv("S3_BUCKET", "")

        self.google_cloud_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

    def validate_required_keys(self) -> list:
        """验证必需的API密钥是否已配置"""
        missing_keys = []

        if not self.openai_api_key:
            missing_keys.append("openai_api_key")

        return missing_keys

    def is_video_gen_configured(self) -> dict:
        """检查哪些视频生成API已配置"""
        return {
            "fal_kling": bool(self.fal_api_key),  # fal.ai Kling v3 Pro
            "kling": bool(self.kling_api_key and self.kling_api_url),
            "sora": bool(self.sora_api_key),
            "seedance": bool(self.seedance_api_key and self.seedance_api_url),
            "veo3": bool(self.veo3_api_key and self.veo3_project_id),
        }


# 全局API密钥实例
api_keys = APIKeys()

# 尝试从环境变量加载
api_keys.load_from_env()
