"""
Redis连接管理
"""
from typing import Optional
import redis.asyncio as redis
from app.core.config import settings


class RedisClient:
    """Redis客户端封装"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """连接到Redis"""
        self.redis = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    
    async def disconnect(self):
        """断开Redis连接"""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        if not self.redis:
            await self.connect()
        return await self.redis.get(key)
    
    async def set(
        self,
        key: str,
        value: str,
        expire: Optional[int] = None
    ) -> bool:
        """设置值"""
        if not self.redis:
            await self.connect()
        return await self.redis.set(key, value, ex=expire)
    
    async def delete(self, key: str) -> int:
        """删除键"""
        if not self.redis:
            await self.connect()
        return await self.redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.redis:
            await self.connect()
        return await self.redis.exists(key) > 0


# 创建全局Redis客户端实例
redis_client = RedisClient()

