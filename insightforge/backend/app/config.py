from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "InsightForge AI"
    app_env: str = "development"

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    parallel_api_key: str = ""

    database_url: str = "sqlite:///./insightforge.db"
    redis_url: str = "redis://redis:6379/0"
    sync_tasks: bool = True

    reports_dir: str = "reports"
    max_sources: int = 20
    strict_no_key_research: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
