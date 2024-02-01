from typing import Optional, Any

from pymemcache.client.base import Client as MemcachedClient

from .base import BaseCache


class MemcachedCache(BaseCache):
    def __init__(self, server: str = 'localhost'):
        self._client = MemcachedClient(server, encoding='utf-8')

    def get(self, key: str) -> Optional[Any]:
        return self._client.get(key)

    def set(self, key: str, value: Any, ttl: int = 0) -> None:
        self._client.set(key, value, ttl)
