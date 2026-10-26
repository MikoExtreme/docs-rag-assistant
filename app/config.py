"""Configuração lida das variáveis de ambiente (ficheiro .env)."""

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    ollama_host: str
    ollama_model: str
    database_url: str
    embedding_model: str
    embedding_dim: int
    chunk_size: int
    chunk_overlap: int
    top_k: int


@lru_cache
def get_settings() -> Settings:
    return Settings(
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "gemma3:12b"),
        database_url=os.getenv("DATABASE_URL", "postgresql://rag:rag@localhost:5432/rag"),
        embedding_model=os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        ),
        embedding_dim=int(os.getenv("EMBEDDING_DIM", "384")),
        chunk_size=int(os.getenv("CHUNK_SIZE", "300")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "50")),
        top_k=int(os.getenv("TOP_K", "5")),
    )
