from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = ""
    app_environment: str = "development"
    secret_key: str = ""
    access_token_minutes: int = 60 * 8
    bootstrap_admin_email: str = ""
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"


settings = Settings()
