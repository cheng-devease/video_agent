"""状态管理器"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from models.workflow_state import WorkflowState, WorkflowStatus
from utils.logger import get_logger
from config.settings import settings

logger = get_logger("state_manager")


class StateManager:
    """工作流状态管理器"""

    def __init__(self, state_dir: str = "./state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def create_state(self, workflow_id: str, product_images: list, user_requirements: str = "") -> WorkflowState:
        """创建新的工作流状态"""
        state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.IDLE,
            product_images=product_images,
            user_requirements=user_requirements,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        self.save_state(state)
        logger.info(f"Created workflow state: {workflow_id}")
        return state

    def save_state(self, state: WorkflowState):
        """保存状态到文件"""
        state.updated_at = datetime.now().isoformat()
        state_file = self.state_dir / f"{state.workflow_id}.json"

        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)

        logger.debug(f"Saved state: {state.workflow_id}")

    def load_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """加载状态"""
        state_file = self.state_dir / f"{workflow_id}.json"

        if not state_file.exists():
            logger.warning(f"State not found: {workflow_id}")
            return None

        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        state = WorkflowState(
            workflow_id=data.get("workflow_id", ""),
            status=WorkflowStatus(data.get("status", "idle")),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            current_step=data.get("current_step", ""),
            current_agent=data.get("current_agent", ""),
            progress=data.get("progress", 0.0),
            product_images=data.get("product_images", []),
            user_requirements=data.get("user_requirements", ""),
            product_info_summary=data.get("product_info_summary", ""),
            creative_plan_summary=data.get("creative_plan_summary", ""),
            scene_images=data.get("scene_images", []),
            video_results_summary=data.get("video_results_summary", ""),
            evaluation_summary=data.get("evaluation_summary", ""),
            final_video_path=data.get("final_video_path", ""),
            error_message=data.get("error_message", ""),
            failed_step=data.get("failed_step", ""),
            metadata=data.get("metadata", {}),
        )

        return state

    def update_state(
        self,
        state: WorkflowState,
        status: Optional[WorkflowStatus] = None,
        step: str = "",
        agent: str = "",
        progress: Optional[float] = None,
        **kwargs,
    ):
        """更新状态"""
        if status:
            state.status = status

        if step:
            state.current_step = step

        if agent:
            state.current_agent = agent

        if progress is not None:
            state.progress = progress

        # 更新其他字段
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)

        self.save_state(state)

    def delete_state(self, workflow_id: str):
        """删除状态"""
        state_file = self.state_dir / f"{workflow_id}.json"
        if state_file.exists():
            state_file.unlink()
            logger.info(f"Deleted state: {workflow_id}")

    def list_workflows(self) -> list:
        """列出所有工作流"""
        workflows = []
        for state_file in self.state_dir.glob("*.json"):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                workflows.append({
                    "workflow_id": data.get("workflow_id"),
                    "status": data.get("status"),
                    "created_at": data.get("created_at"),
                    "progress": data.get("progress"),
                })
            except Exception as e:
                logger.warning(f"Failed to read state file {state_file}: {e}")

        return workflows

    def compress_state(self, state: WorkflowState) -> Dict[str, Any]:
        """压缩状态（用于上下文管理）"""
        return state.get_compressed_state()
