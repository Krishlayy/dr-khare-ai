from pathlib import Path

from pydantic_settings import BaseSettings

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "Dr Khare AI Assistant"
    DATABASE_URL: str = f"sqlite:///{BACKEND_DIR / 'app.db'}"
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
    LLM_PROVIDER: str = "groq" # defaults to groq, falls back to ollama if no key
    
    ENABLE_LLM_BYPASS: bool = False
    BYPASS_CONFIDENCE_THRESHOLD: float = 0.90
    
    SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    UPLOAD_DIR: str = str(PROJECT_ROOT / "storage" / "uploads")
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]
    TOP_K_CHUNKS: int = 3          # 3 chunks → smaller prompt → faster response
    SIMILARITY_THRESHOLD: float = 0.40
    WEB_FALLBACK_THRESHOLD: float = 0.0
    MEMORY_WINDOW: int = 4         # 4 messages of history (was 6) → smaller prompt
    RATE_LIMIT: str = "60/minute"
    CHAT_RATE_LIMIT: str = "30/minute"
    ENVIRONMENT: str = "development"
    TAVILY_API_KEY: str = ""

    from pydantic import model_validator
    @model_validator(mode='after')
    def validate_secret_key(self):
        if self.ENVIRONMENT == "production" and self.SECRET_KEY == "your-super-secret-jwt-key-change-in-production":
            raise ValueError("SECRET_KEY must be overridden in production environment")
        return self

    class Config:
        env_file = ".env"

settings = Settings()
