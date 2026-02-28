from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "InsightForge AI"
    app_env: str = "development"

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    parallel_api_key: str = ""

    database_url: str = "postgresql://insightforge:insightforge@postgres:5432/insightforge"
    redis_url: str = "redis://redis:6379/0"

    reports_dir: str = "reports"
    max_sources: int = 20

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
