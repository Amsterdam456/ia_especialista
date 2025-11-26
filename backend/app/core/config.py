# app/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ROTAS
    API_V1_PREFIX: str = "/athena"

    # Embeddings
    EMBEDDINGS_FILE: str = "data/embeddings.pkl"
    POLICY_DIR: str = "policies"

    # LM Studio
    LMSTUDIO_API_URL: str = "http://localhost:1234/v1/chat/completions"
    LMSTUDIO_MODEL: str = "phi-3.5-mini-3.8b-arliai-rpmax-v1.1"

    # Watcher
    CHECK_INTERVAL_SECONDS: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"  # IGNORA variáveis extras no .env


# 👈 Agora o settings existe corretamente
settings = Settings()
