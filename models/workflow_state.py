"""工作流状态模型"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
import json
from datetime import datetime


class WorkflowStatus(Enum):
    """工作流状态"""
    IDLE = "idle"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    GENERATING_SCENES = "generating_scenes"
    GENERATING_PROMPTS = "generating_prompts"
    GENERATING_VIDEOS = "generating_videos"
    EVALUATING = "evaluating"
    EDITING = "editing"
    COMPOSING = "composing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowState:
    """工作流状态模型"""

    # 基本信息
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.IDLE

    # 时间信息
    created_at: str = ""
    updated_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    # 当前步骤
    current_step: str = ""
    current_agent: str = ""
    progress: float = 0.0  # 0-100

    # 输入
    product_images: list = field(default_factory=list)
    user_requirements: str = ""

    # 各阶段结果 (压缩存储)
    product_info_summary: str = ""
    creative_plan_summary: str = ""
    scene_images: list = field(default_factory=list)
    video_results_summary: str = ""
    evaluation_summary: str = ""

    # 最终输出
    final_video_path: str = ""

    # 错误信息
    error_message: str = ""
    failed_step: str = ""

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def update_status(self, status: WorkflowStatus, step: str = "", agent: str = ""):
        """更新状态"""
        self.status = status
        self.current_step = step
        self.current_agent = agent
        self.updated_at = datetime.now().isoformat()

    def set_progress(self, progress: float):
        """设置进度"""
        self.progress = min(100.0, max(0.0, progress))
        self.updated_at = datetime.now().isoformat()

    def mark_started(self):
        """标记开始"""
        self.started_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def mark_completed(self, final_video_path: str = ""):
        """标记完成"""
        self.status = WorkflowStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.progress = 100.0
        self.final_video_path = final_video_path

    def mark_failed(self, error_message: str, failed_step: str = ""):
        """标记失败"""
        self.status = WorkflowStatus.FAILED
        self.error_message = error_message
        self.failed_step = failed_step
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "current_step": self.current_step,
            "current_agent": self.current_agent,
            "progress": self.progress,
            "product_images": self.product_images,
            "user_requirements": self.user_requirements,
            "final_video_path": self.final_video_path,
            "error_message": self.error_message,
            "failed_step": self.failed_step,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def get_compressed_state(self) -> dict:
        """获取压缩后的状态（用于上下文管理）"""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "progress": self.progress,
            "current_step": self.current_step,
            "product_info_summary": self.product_info_summary,
            "creative_plan_summary": self.creative_plan_summary,
            "final_video_path": self.final_video_path,
        }
