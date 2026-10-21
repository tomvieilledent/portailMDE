from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "portailMDE"
    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://portail:change-me@db:5432/portail"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    cors_origins: list[str] = ["http://localhost:5290"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
