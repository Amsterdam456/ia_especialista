from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "ATHENA"

    EMBEDDINGS_FILE: str = "data/embeddings.pkl"
    POLICY_DIR: str = "policies"

    LMSTUDIO_API_URL: str = "http://127.0.0.1:1234/v1/responses"
    LMSTUDIO_MODEL: str = "qwen2.5-7b-instruct-1m"

    CHECK_INTERVAL_SECONDS: int = 30

    SECRET_KEY: str = Field("change-me", min_length=8)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720

    DATABASE_URL: str = "sqlite:///./data/athena.db"

    ADMIN_EMAIL: str = "admin@athena.local"
    ADMIN_PASSWORD: str = "admin123"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
