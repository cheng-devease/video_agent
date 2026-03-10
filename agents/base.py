"""Agent基类"""
from abc import ABC, abstractmethod
from typing import Any, Optional
from utils.logger import get_logger


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"agent.{name}")

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """执行Agent任务"""
        pass

    def log_start(self, action: str):
        """记录开始"""
        self.logger.info(f"[{self.name}] Starting: {action}")

    def log_complete(self, action: str, result: Optional[str] = None):
        """记录完成"""
        msg = f"[{self.name}] Completed: {action}"
        if result:
            msg += f" -> {result[:100]}..."
        self.logger.info(msg)

    def log_error(self, action: str, error: Exception):
        """记录错误"""
        self.logger.error(f"[{self.name}] Error in {action}: {error}")
