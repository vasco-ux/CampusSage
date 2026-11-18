import os
from pydantic_settings import BaseSettings
from typing import Optional

def _detect_production() -> bool:
    """Returns True if running in a cloud deployment environment (e.g. Render, Railway, Vercel)."""
    return bool(os.getenv("RENDER") or os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENVIRONMENT") == "production")

class Settings(BaseSettings):
    APP_NAME: str = "CampusSage"
    ENVIRONMENT: str = "production" if _detect_production() else "development"
    DEBUG: bool = False if _detect_production() else True
    
    # Paths (Resolved dynamically relative to backend root)
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    PDF_DIR: str = os.path.join(DATA_DIR, "raw_pdfs")
    CHROMA_DIR: str = os.path.join(DATA_DIR, "chroma_db")
    MODELS_DIR: str = os.path.join(DATA_DIR, "models")
    DATABASE_URL: str = f"sqlite:///{os.path.join(DATA_DIR, 'campussage.db')}"

    # Vector Storage & Embeddings
    CHROMA_COLLECTION: str = "campus_notices"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 700
    CHUNK_OVERLAP: int = 120
    SIMILARITY_TOP_K: int = 4

    # LLM Settings: In production (Render), default to "groq". In local dev, default to "ollama".
    LLM_PROVIDER: str = "groq" if _detect_production() else "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3:8b"
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure critical data directories exist
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.PDF_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_DIR, exist_ok=True)
os.makedirs(settings.MODELS_DIR, exist_ok=True)

# Set model cache inside workspace
os.environ["HF_HOME"] = settings.MODELS_DIR
os.environ["SENTENCE_TRANSFORMERS_HOME"] = settings.MODELS_DIR
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
