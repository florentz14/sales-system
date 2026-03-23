from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    secret_key: str = "change-me-in-production-use-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    database_url: str = "sqlite:///./sales.db"

    api_v1_prefix: str = "/api/v1"

    # Salida por defecto para reportes generados desde CLI
    reports_output_dir: str = "var/reports"


@lru_cache
def get_settings() -> Settings:
    return Settings()
