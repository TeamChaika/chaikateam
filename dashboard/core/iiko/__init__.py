from core.cache import memcached_cache
from .api import IikoApi

iiko_api = IikoApi(cache=memcached_cache)
