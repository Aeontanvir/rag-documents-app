from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"


class Settings(BaseSettings):
    app_name: str = "Doc AI"
    api_v1_prefix: str = "/api/v1"
    chroma_collection_name: str = "doc_ai_knowledge_base"

    storage_dir: Path = STORAGE_DIR
    uploads_dir: Path = STORAGE_DIR / "uploads"
    chroma_dir: Path = STORAGE_DIR / "chroma"
    manifest_path: Path = STORAGE_DIR / "documents.json"

    chunk_size: int = Field(default=1200, ge=200)
    chunk_overlap: int = Field(default=200, ge=0)
    retrieval_k: int = Field(default=6, ge=1)

    llm_provider: str = "ollama"
    llm_model: str = "llama3.1:8b"
    embedding_provider: str = "ollama"
    embedding_model: str = "nomic-embed-text"
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def ensure_storage(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        if not self.manifest_path.exists():
            self.manifest_path.write_text("[]", encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_storage()
    return settings
