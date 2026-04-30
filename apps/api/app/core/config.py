from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Site Yonetim API"
    app_version: str = "0.1.0"
    app_env: str = Field(default="development", alias="APP_ENV")
    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(
        default="postgresql+psycopg://saas_user:change_me@localhost:5432/saas_db",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
