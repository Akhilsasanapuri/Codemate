from functools import lru_cache
from typing import List

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Provider-agnostic LLM config (uses any OpenAI-compatible endpoint:
    # Gemini, Groq, OpenRouter, Ollama, OpenAI itself, etc.)
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai/",
        alias="LLM_BASE_URL",
    )
    llm_model: str = Field(default="gemini-2.5-flash-lite", alias="LLM_MODEL")
    llm_timeout_seconds: float = Field(default=30.0, alias="LLM_TIMEOUT_SECONDS")

    # Embeddings (Gemini native REST; OpenAI-compat endpoint does not expose /embeddings).
    embedding_model: str = Field(default="gemini-embedding-001", alias="EMBEDDING_MODEL")
    embedding_dim: int = Field(default=768, alias="EMBEDDING_DIM")
    embedding_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta",
        alias="EMBEDDING_BASE_URL",
    )

    # Vector store
    chroma_dir: str = Field(default="./chroma_db", alias="CHROMA_DIR")
    rag_top_k: int = Field(default=6, alias="RAG_TOP_K")

    # Codebase ingest safety caps
    max_file_bytes: int = Field(default=100 * 1024, alias="MAX_FILE_BYTES")  # 100 KB
    max_files_per_project: int = Field(default=500, alias="MAX_FILES_PER_PROJECT")
    max_chunks_per_project: int = Field(default=2000, alias="MAX_CHUNKS_PER_PROJECT")

    db_url: str = Field(default="sqlite:///./codemate.db", alias="DB_URL")
    cors_origins_raw: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        alias="CORS_ORIGINS",
    )

    @computed_field  # type: ignore[misc]
    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
