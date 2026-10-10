"""Validated configuration; no models or private documents accessed at import."""
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(__file__).resolve().parent / "data" / "v2"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ollama_url: str = "http://127.0.0.1:11434"
    model: str = "llama3"
    chunk_size: int = 800
    chunk_overlap: int = 100
    top_k: int = 3
    min_score: float = 0.30
    max_upload_bytes: int = 25 * 1024 * 1024
    max_chunks: int = 3000
    max_concurrent: int = 2
    generation_timeout: float = 120
    api_token: str = ""
    cors_origins: tuple = ("http://127.0.0.1:5500", "http://localhost:5500", "http://127.0.0.1:5173", "http://localhost:5173")

    def __post_init__(self):
        if not (0 <= self.chunk_overlap < self.chunk_size):
            raise ValueError("Chunk overlap must be smaller than chunk size.")
        if not (-1 <= self.min_score <= 1):
            raise ValueError("Minimum cosine score must be between -1 and 1.")
        if min(self.top_k, self.max_upload_bytes, self.max_chunks, self.max_concurrent, self.generation_timeout) <= 0:
            raise ValueError("Resource limits must be positive.")
        if not self.ollama_url.startswith(("http://", "https://")):
            raise ValueError("Ollama URL must be HTTP(S).")

    @classmethod
    def from_env(cls):
        types = {"data_dir": Path, "chunk_size": int, "chunk_overlap": int, "top_k": int, "min_score": float, "max_upload_bytes": int, "max_chunks": int, "max_concurrent": int, "generation_timeout": float}
        names = {"data_dir": "ADI_DATA_DIR", "embedding_model": "EMBEDDING_MODEL", "ollama_url": "OLLAMA_BASE_URL", "model": "OLLAMA_MODEL", "chunk_size": "CHUNK_SIZE", "chunk_overlap": "CHUNK_OVERLAP", "top_k": "TOP_K", "min_score": "MIN_RETRIEVAL_SCORE", "max_upload_bytes": "MAX_UPLOAD_BYTES", "max_chunks": "MAX_CHUNKS", "max_concurrent": "MAX_CONCURRENT_REQUESTS", "generation_timeout": "GENERATION_TIMEOUT", "api_token": "ADI_API_TOKEN"}
        values = {field: types.get(field, str)(os.getenv(env, str(getattr(cls, field)))) for field, env in names.items()}
        values["data_dir"] = values["data_dir"].resolve()
        values["ollama_url"] = values["ollama_url"].rstrip("/")
        values["cors_origins"] = tuple(x.strip() for x in os.getenv("CORS_ORIGINS", ",".join(cls.cors_origins)).split(",") if x.strip())
        return cls(**values)
