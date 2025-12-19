from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "ATHENA"

    EMBEDDINGS_FILE: str = "data/embeddings.pkl"
    POLICY_DIR: str = "storage/policies"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    LMSTUDIO_API_URL: str = "http://127.0.0.1:1234/v1/responses"
    LMSTUDIO_MODEL: str = "qwen2.5-7b-instruct-1m"
    LMSTUDIO_TIMEOUT_SECONDS: int = 900

    CHECK_INTERVAL_SECONDS: int = 86400  # 24h para watcher
    FINANCE_CSV_PATH: str = "data/finance.csv"
    FINANCE_REFRESH_SECONDS: int = 86400

    SECRET_KEY: str = Field("change-me", min_length=8)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720

    DATABASE_URL: str = "sqlite:///./data/athena.db"

    ADMIN_EMAIL: str = "admin@athena.com"
    ADMIN_PASSWORD: str = "change-me"

    PASSWORD_MIN_LENGTH: int = 8
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_MAX_REQUESTS: int = 30
    MAX_UPLOAD_MB: int = 20
    MAX_QUESTION_CHARS: int = 2000
    FEEDBACK_DIRECTIVES_LIMIT: int = 20

    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
