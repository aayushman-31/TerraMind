from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Darukaa Biodiversity Intelligence Agent"
    app_env: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    database_url: str = "sqlite+pysqlite:///./data/darukaa.db"

    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    embedding_backend: str = "hashing"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    retrieval_config_path: str = "config/retrieval.yaml"
    relationship_graph_path: str = "config/environmental_graph.yaml"
    interventions_path: str = "config/interventions.yaml"
    corpus_path: str = "knowledge/corpus"

    rate_limit_per_minute: int = 60
    cors_origins: str = "http://localhost:8080,http://localhost:3000,http://127.0.0.1:8080"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def uses_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")


@lru_cache
def get_settings() -> Settings:
    return Settings()
