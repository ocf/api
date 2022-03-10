from pydantic import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    ocfstats_user: str
    ocfstats_password: str
    ocfstats_db: str

    redis_host: str
    redis_port: str
    redis_password: str

    debug: bool = False
    version: str = "dev"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
