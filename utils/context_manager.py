"""上下文管理器 - 支持LLM调用上下文和工作流状态的压缩"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import tiktoken
from utils.logger import get_logger

logger = get_logger("context_manager")


@dataclass
class Message:
    """消息模型"""
    role: str  # system, user, assistant
    content: str
    tokens: int = 0


class ContextCompressor:
    """上下文压缩器"""

    def __init__(
        self,
        model: str = "gpt-4",
        max_tokens: int = 128000,
        compression_threshold: float = 0.6,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.compression_threshold = compression_threshold
        self.encoding = tiktoken.encoding_for_model(model)

    def count_tokens(self, text: str) -> int:
        """计算token数量"""
        return len(self.encoding.encode(text))

    def count_messages_tokens(self, messages: List[Message]) -> int:
        """计算消息列表的总token数"""
        total = 0
        for msg in messages:
            total += msg.tokens or self.count_tokens(msg.content)
            total += 4  # 消息格式开销
        return total

    def should_compress(self, messages: List[Message]) -> bool:
        """判断是否需要压缩"""
        current_tokens = self.count_messages_tokens(messages)
        threshold_tokens = int(self.max_tokens * self.compression_threshold)
        return current_tokens >= threshold_tokens

    async def compress_messages(
        self,
        messages: List[Message],
        llm_client,
        compression_prompt: str = "",
    ) -> List[Message]:
        """压缩消息历史"""
        if not self.should_compress(messages):
            return messages

        logger.info(f"Compressing context: {len(messages)} messages")

        # 保留系统消息
        system_messages = [m for m in messages if m.role == "system"]

        # 需要压缩的消息
        to_compress = [m for m in messages if m.role != "system"]

        if len(to_compress) <= 2:
            return messages

        # 构建压缩请求
        conversation_text = "\n".join([
            f"{m.role}: {m.content}"
            for m in to_compress[:-2]  # 保留最后2条消息
        ])

        prompt = compression_prompt or f"""
请将以下对话历史压缩为简洁的摘要，保留所有关键决策、结论和重要信息:

{conversation_text}

摘要:
"""

        # 调用LLM进行压缩
        try:
            response = await llm_client.generate(prompt)
            summary = response.strip()

            # 构建新的消息列表
            compressed_message = Message(
                role="user",
                content=f"[历史对话摘要]\n{summary}",
                tokens=self.count_tokens(summary),
            )

            new_messages = system_messages + [compressed_message] + to_compress[-2:]
            logger.info(f"Context compressed: {len(messages)} -> {len(new_messages)} messages")
            return new_messages

        except Exception as e:
            logger.error(f"Failed to compress context: {e}")
            return messages


class ContextManager:
    """上下文管理器"""

    def __init__(
        self,
        model: str = "gpt-4",
        max_tokens: int = 128000,
        compression_threshold: float = 0.6,
    ):
        self.compressor = ContextCompressor(
            model=model,
            max_tokens=max_tokens,
            compression_threshold=compression_threshold,
        )
        self._messages: List[Message] = []
        self._state_cache: Dict[str, Any] = {}

    def add_message(self, role: str, content: str):
        """添加消息"""
        message = Message(
            role=role,
            content=content,
            tokens=self.compressor.count_tokens(content),
        )
        self._messages.append(message)

    def get_messages(self) -> List[Dict[str, str]]:
        """获取消息列表"""
        return [{"role": m.role, "content": m.content} for m in self._messages]

    def get_token_count(self) -> int:
        """获取当前token数量"""
        return self.compressor.count_messages_tokens(self._messages)

    def should_compress(self) -> bool:
        """是否需要压缩"""
        return self.compressor.should_compress(self._messages)

    async def compress_if_needed(self, llm_client, compression_prompt: str = ""):
        """如果需要则压缩"""
        self._messages = await self.compressor.compress_messages(
            self._messages, llm_client, compression_prompt
        )

    def clear(self):
        """清空上下文"""
        self._messages.clear()
        self._state_cache.clear()

    # 工作流状态压缩
    def compress_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """压缩工作流状态"""
        compressed = {
            "workflow_id": state.get("workflow_id"),
            "status": state.get("status"),
            "progress": state.get("progress"),
            "current_step": state.get("current_step"),
        }

        # 压缩大型数据
        if "product_info" in state:
            pi = state["product_info"]
            compressed["product_info_summary"] = {
                "type": pi.get("product_type"),
                "name": pi.get("product_name"),
            }

        if "creative_plan" in state:
            cp = state["creative_plan"]
            compressed["creative_plan_summary"] = {
                "style": cp.get("ad_style"),
                "scene_count": len(cp.get("scenes", [])),
            }

        return compressed

    def save_state(self, key: str, state: Any):
        """保存状态"""
        self._state_cache[key] = state

    def get_state(self, key: str) -> Optional[Any]:
        """获取状态"""
        return self._state_cache.get(key)

    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return {
            "message_count": len(self._messages),
            "total_tokens": self.get_token_count(),
            "usage_percentage": self.get_token_count() / self.compressor.max_tokens * 100,
            "state_cache_size": len(self._state_cache),
        }
