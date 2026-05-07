from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    runway_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    telegram_bot_token: str = ""
    base_url: str = "http://localhost:8000"
    database_url: str = "sqlite:///./recall.db"
    demo_password: str = ""
    storage_dir: str = "./storage"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

