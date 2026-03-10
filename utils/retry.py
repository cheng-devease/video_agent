"""重试机制"""
import asyncio
import functools
from typing import Callable, Type, Tuple
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from utils.logger import get_logger

logger = get_logger("retry")


def async_retry(
    max_attempts: int = 3,
    wait_min: float = 1.0,
    wait_max: float = 30.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """异步重试装饰器"""

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    wait_time = min(wait_min * (2**attempt), wait_max)
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(wait_time)

            logger.error(f"All {max_attempts} attempts failed")
            raise last_exception

        return wrapper

    return decorator


def sync_retry(
    max_attempts: int = 3,
    wait_min: float = 1.0,
    wait_max: float = 30.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """同步重试装饰器"""

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    wait_time = min(wait_min * (2**attempt), wait_max)
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    if attempt < max_attempts - 1:
                        time.sleep(wait_time)

            logger.error(f"All {max_attempts} attempts failed")
            raise last_exception

        return wrapper

    return decorator


# 使用tenacity的重试配置
def get_retry_config(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 30.0,
):
    """获取tenacity重试配置"""
    return {
        "stop": stop_after_attempt(max_attempts),
        "wait": wait_exponential(multiplier=min_wait, max=max_wait),
        "before_sleep": before_sleep_log(logger, "WARNING"),
        "reraise": True,
    }
