from functools import lru_cache

from pydantic import model_validator
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
    upload_dir: str = "uploads"
    max_image_bytes: int = 5 * 1024 * 1024
    max_document_bytes: int = 15 * 1024 * 1024
    cors_origins: list[str] = ["http://localhost:5290"]

    @model_validator(mode="after")
    def _refuse_default_secret_in_production(self):
        if self.environment == "production" and (
            self.jwt_secret == "dev-secret-change-me" or len(self.jwt_secret) < 32
        ):
            raise ValueError("JWT_SECRET doit être défini (32 caractères minimum) en production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
