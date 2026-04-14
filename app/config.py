from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./crypto.db"
    api_secret_key: str = "change-me-in-production"
    line_notify_token: str = ""
    openai_api_key: str = ""
    alert_score_threshold: int = 60
    monitor_interval_minutes: int = 10
    daily_summary_hour: int = 9

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
