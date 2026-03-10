"""缓存管理"""
import hashlib
import json
import asyncio
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timedelta
import aiofiles
from utils.logger import get_logger

logger = get_logger("cache")


class CacheManager:
    """缓存管理器"""

    def __init__(self, cache_dir: str = "./cache", ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl  # 默认缓存时间(秒)
        self._memory_cache = {}  # 内存缓存

    def _get_cache_key(self, key: str) -> str:
        """生成缓存键"""
        return hashlib.md5(key.encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        cache_key = self._get_cache_key(key)
        return self.cache_dir / f"{cache_key}.json"

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        # 先检查内存缓存
        if key in self._memory_cache:
            cached = self._memory_cache[key]
            if datetime.now() < cached["expires"]:
                logger.debug(f"Memory cache hit: {key}")
                return cached["data"]
            else:
                del self._memory_cache[key]

        # 检查文件缓存
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                async with aiofiles.open(cache_path, "r") as f:
                    content = await f.read()
                    cached = json.loads(content)

                expires = datetime.fromisoformat(cached["expires"])
                if datetime.now() < expires:
                    logger.debug(f"File cache hit: {key}")
                    return cached["data"]
                else:
                    cache_path.unlink()  # 删除过期缓存
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}")

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        ttl = ttl or self.ttl
        expires = datetime.now() + timedelta(seconds=ttl)

        cached = {
            "data": value,
            "expires": expires.isoformat(),
            "created": datetime.now().isoformat(),
        }

        # 存入内存
        self._memory_cache[key] = cached

        # 存入文件
        cache_path = self._get_cache_path(key)
        try:
            async with aiofiles.open(cache_path, "w") as f:
                await f.write(json.dumps(cached, ensure_ascii=False, indent=2))
            logger.debug(f"Cache set: {key}")
        except Exception as e:
            logger.warning(f"Failed to write cache: {e}")

    async def delete(self, key: str):
        """删除缓存"""
        if key in self._memory_cache:
            del self._memory_cache[key]

        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()

        logger.debug(f"Cache deleted: {key}")

    async def clear(self):
        """清空所有缓存"""
        self._memory_cache.clear()

        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()

        logger.info("Cache cleared")

    async def cleanup_expired(self):
        """清理过期缓存"""
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                async with aiofiles.open(cache_file, "r") as f:
                    content = await f.read()
                    cached = json.loads(content)

                expires = datetime.fromisoformat(cached["expires"])
                if datetime.now() >= expires:
                    cache_file.unlink()
                    count += 1
            except Exception:
                pass

        logger.info(f"Cleaned up {count} expired cache files")

    def get_sync(self, key: str) -> Optional[Any]:
        """同步获取缓存"""
        if key in self._memory_cache:
            cached = self._memory_cache[key]
            if datetime.now() < cached["expires"]:
                return cached["data"]
        return None

    def set_sync(self, key: str, value: Any, ttl: Optional[int] = None):
        """同步设置缓存"""
        ttl = ttl or self.ttl
        expires = datetime.now() + timedelta(seconds=ttl)
        self._memory_cache[key] = {
            "data": value,
            "expires": expires,
        }
