from __future__ import annotations

import hashlib
import math
import re
from functools import lru_cache

import numpy as np

from app.config.settings import get_settings

TOKEN_RE = re.compile(r"[a-z0-9%]+", re.I)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


class EmbeddingProvider:
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class HashingEmbeddingProvider(EmbeddingProvider):
    """Deterministic n-gram hashing embeddings. No model download required."""

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = np.zeros(self.dim, dtype=np.float64)
        tokens = tokenize(text)
        grams = tokens + [" ".join(tokens[i : i + 2]) for i in range(len(tokens) - 1)]
        for gram in grams:
            digest = hashlib.sha256(gram.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "little") % self.dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[idx] += sign
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.astype(float).tolist()


class SentenceTransformerProvider(EmbeddingProvider):
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return [row.astype(float).tolist() for row in np.asarray(vectors)]


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.embedding_backend == "sentence-transformers":
        return SentenceTransformerProvider(settings.embedding_model)
    return HashingEmbeddingProvider(settings.embedding_dim)


def cosine(a: list[float], b: list[float]) -> float:
    va = np.asarray(a, dtype=np.float64)
    vb = np.asarray(b, dtype=np.float64)
    denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def lexical_overlap(query: str, text: str) -> float:
    q = set(tokenize(query))
    t = set(tokenize(text))
    if not q or not t:
        return 0.0
    return len(q & t) / math.sqrt(len(q) * len(t))
