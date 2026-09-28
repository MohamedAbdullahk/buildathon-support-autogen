from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str = ""
    SERPER_API_KEY: str = ""

    # App Settings
    LLM_MODEL: str = "gpt-4.1-mini"
    DATA_DIR: str = "./data"
    LOG_DIR: str = "./logs"
    BACKEND_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()