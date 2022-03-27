from functools import lru_cache

import redis

from utils.config import get_settings


@lru_cache()
def get_redis_connection():
    settings = get_settings()

    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
    )
