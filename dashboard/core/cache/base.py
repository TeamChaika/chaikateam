from abc import ABC
from typing import Optional, Any


class BaseCache(ABC):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(BaseCache, cls).__new__(
                cls, *args, **kwargs
            )
        return cls._instance

    def get(self, key: str) -> Optional[Any]:
        return NotImplemented

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        return NotImplemented
