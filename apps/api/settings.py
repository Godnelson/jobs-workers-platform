from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    env: str = "dev"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8080

    database_url: str  # DATABASE_URL (no APP_ prefix; loaded via env_file too)
    redis_url: str  # REDIS_URL
    rq_queue_name: str = "default"  # RQ_QUEUE_NAME


def load_settings() -> "Settings":
    # Allow both APP_* and raw vars like DATABASE_URL/REDIS_URL
    s = Settings()
    return s
