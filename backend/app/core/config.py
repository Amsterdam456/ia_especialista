# app/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ROTAS
    API_V1_PREFIX: str = "/api/v1"

    # Embeddings
    EMBEDDINGS_FILE: str = "data/embeddings.pkl"
    POLICY_DIR: str = "policies"

    # LM Studio
    LMSTUDIO_API_URL: str = "http://localhost:1234/v1/chat/completions"
    LMSTUDIO_MODEL: str = "phi-3.5-mini-3.8b-arliai-rpmax-v1.1"

    # Watcher
    CHECK_INTERVAL_SECONDS: int = 30

    # Auth
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720

    # Database
    DATABASE_URL: str = "sqlite:///./data/athena.db"

    # Admin bootstrap
    ADMIN_EMAIL: str = "admin@athena.local"
    ADMIN_PASSWORD: str = "admin123"

    class Config:
        env_file = ".env"
        extra = "ignore"  # IGNORA variáveis extras no .env


# 👈 Agora o settings existe corretamente
settings = Settings()
