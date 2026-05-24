import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App General Settings
    APP_NAME: str = "Agentic Knowledge OS"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # LLM Settings
    # Supports "openai", "gemini", or "ollama"
    PRIMARY_LLM_PROVIDER: str = "gemini" 
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Model Configurations
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"
    GEMINI_CHAT_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBED_MODEL: str = "models/text-embedding-004"
    OLLAMA_CHAT_MODEL: str = "llama3"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    
    # Embedding Configuration
    # Supports "openai", "gemini", "ollama", or "local" (HuggingFace)
    EMBEDDING_PROVIDER: str = "local"
    LOCAL_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Qdrant Settings
    # Supports "local" (in-memory/disk) or "server" (docker-compose)
    QDRANT_MODE: str = "local"
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "agentic_knowledge_os"
    
    # SQLite Database Path for Task Management
    SQLITE_DB_PATH: str = "data/processed/tasks.db"
    
    # Raw Files Path
    UPLOAD_DIR: str = "data/raw"
    PROCESSED_DIR: str = "data/processed"
    
    # Observability
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    
    # RAG Settings
    HYBRID_ALPHA: float = 0.5  # Weight for vector search vs BM25: alpha * vector + (1 - alpha) * BM25
    TOP_K: int = 8
    USE_RERANKER: bool = False
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.SQLITE_DB_PATH), exist_ok=True)
