from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    ocfstats_user: str = "waddles"
    ocfstats_password: str = "shhverysecret"
    ocfstats_db: str = "ocfstats"

    ocfprinting_user: str = "waddles"
    ocfprinting_password: str = "shhverysecret"
    ocfprinting_db: str = "ocfprinting"

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_password: str = "shhverysecret"

    celery_broker: str = "redis://127.0.0.1:6378"
    celery_backend: str = "redis://127.0.0.1:6378"

    debug: bool = False
    version: str = "dev"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
