from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from app.config.settings import get_settings


@dataclass
class RetrievalWeights:
    semantic_weight: float
    lexical_weight: float
    domain_weight: float
    geographic_weight: float
    metric_weight: float
    top_k: int
    rerank_k: int
    min_evidence_score: float


def load_retrieval_weights() -> RetrievalWeights:
    settings = get_settings()
    path = Path(settings.retrieval_config_path)
    if not path.is_file():
        path = Path(__file__).resolve().parents[2] / "config" / "retrieval.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))["retrieval"]
    return RetrievalWeights(**data)
