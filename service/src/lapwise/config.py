from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openf1_base_url: str = "https://api.openf1.org/v1"
    openf1_timeout_seconds: float = 10.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
