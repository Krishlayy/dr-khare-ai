import os
from pathlib import Path

from pydantic_settings import BaseSettings

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "Dr Khare AI Assistant"
    DATABASE_URL: str
    CHROMA_PATH: str = str(BACKEND_DIR / "chroma_db")
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL_PRIORITY: list[str] = [
        "qwen2.5:3b",
        "phi3:mini",
        "qwen2.5:7b",
        "llama3:latest",
    ]
    OLLAMA_NUM_GPU: int | None = None
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    LLM_PROVIDER: str = "groq" # defaults to groq, falls back to ollama if no key
    PRIMARY_PROVIDER: str = "groq"
    FALLBACK_PROVIDER: str = "ollama"
    
    ENABLE_LLM_BYPASS: bool = False
    BYPASS_CONFIDENCE_THRESHOLD: float = 0.90
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    UPLOAD_DIR: str = str(PROJECT_ROOT / "storage" / "uploads")
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]
    TOP_K_CHUNKS: int = 5          # 5 chunks → better recall
    SIMILARITY_THRESHOLD: float = 0.10  # Rejection threshold
    SIMILARITY_THRESHOLD_CAUTIOUS: float = 0.25 # Medium confidence threshold
    WEB_FALLBACK_THRESHOLD: float = 0.0
    MEMORY_WINDOW: int = 4         # 4 messages of history (was 6) → smaller prompt
    RATE_LIMIT: str = "60/minute"
    CHAT_RATE_LIMIT: str = "30/minute"
    ENVIRONMENT: str = "development"
    TAVILY_API_KEY: str = ""

    # Infrastructure Config
    REDIS_URL: str | None = None
    SENTRY_DSN: str | None = None
    
    # S3 Config
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_BUCKET_NAME: str | None = None
    AWS_REGION: str = "us-east-1"
    AWS_ENDPOINT_URL: str | None = None

    class Config:
        env_file = os.environ.get("ENV_FILE", ".env")

settings = Settings()
