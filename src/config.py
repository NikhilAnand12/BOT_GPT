"""Configuration settings for BOT GPT."""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""

    groq_api_key: str

    # Database
    database_url: str = "sqlite:///./data/bot_gpt.db"

    # ChromaDB
    chromadb_path: str = "./data/chromadb"

    # File uploads
    upload_dir: str = "./data/uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # LLM Settings
    llm_model: str = "llama-3.1-8b-instant"
    max_context_tokens: int = 8000
    max_response_tokens: int = 512

    # RAG Settings
    chunk_size: int = 2000
    chunk_overlap: int = 200
    top_k_chunks: int = 5
    similarity_threshold: float = 0.7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create settings instance
settings = Settings()

# Create necessary directories
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.chromadb_path).mkdir(parents=True, exist_ok=True)
Path("data").mkdir(exist_ok=True)
