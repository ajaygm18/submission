from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SkillBridge Attendance API"
    database_url: str = "sqlite:///./skillbridge.db"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_hours: int = 24
    monitoring_token_expire_hours: int = 1
    monitoring_api_key: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
