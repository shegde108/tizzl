from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    chroma_persist_directory: str = "./chroma_db"
    redis_url: str = "redis://localhost:6379"
    environment: str = "development"
    log_level: str = "INFO"
    
    max_items_per_query: int = 20
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: int = 2000
    
    embedding_dimension: int = 1536
    similarity_threshold: float = 0.7
    rerank_top_k: int = 50
    final_top_k: int = 15
    
    cache_ttl: int = 3600
    enable_cache: bool = True
    
    api_cors_origins: list = ["*"]
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()