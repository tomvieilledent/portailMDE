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
    upload_dir: str = "uploads"
    max_image_bytes: int = 5 * 1024 * 1024
    max_document_bytes: int = 15 * 1024 * 1024
    news_sync_enabled: bool = True
    news_sync_interval_minutes: int = 60
    news_retention_days: int = 30
    frontend_url: str = "http://localhost:5290"
    mail_backend: str = "smtp"  # "smtp" | "console" | "memory" (tests)
    mail_host: str = "mailpit"
    mail_port: int = 1025
    mail_username: str = ""
    mail_password: str = ""
    mail_use_tls: bool = False
    mail_from: str = "portailMDE <no-reply@portail-mde.local>"
    reset_token_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:5290"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
