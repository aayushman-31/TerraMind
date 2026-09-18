from __future__ import annotations

from app.retrieval.embeddings import tokenize
from app.schemas.environment import EnvironmentalState


def build_retrieval_query(
    user_message: str,
    state: EnvironmentalState,
    problem: str | None = None,
    candidate_intervention: str | None = None,
    extra_terms: list[str] | None = None,
) -> str:
    parts: list[str] = []
    if user_message:
        parts.extend(tokenize(user_message)[:40])
    known = state.known_paths()
    for path, obs in known.items():
        parts.append(path.replace(".", " "))
        parts.append(str(obs.value))
    if state.scalar("land.crop"):
        parts.append(str(state.scalar("land.crop")))
    if state.scalar("land.cropping_system"):
        parts.append(str(state.scalar("land.cropping_system")))
    if str(state.scalar("climate.rainfall")).lower() in {"low", "very_low", "drought"}:
        parts.extend(["low rainfall", "drought", "water availability", "semi-arid agriculture"])
    if _is_low_soc(state):
        parts.extend(["low soil organic carbon", "soil biodiversity", "soil health"])
    if str(state.scalar("land.cropping_system") or "").lower() in {
        "monoculture",
        "continuous_monoculture",
    }:
        parts.extend(["wheat monoculture", "habitat diversity", "intercropping", "agroforestry"])
    if problem:
        parts.append(problem)
    if candidate_intervention:
        parts.append(candidate_intervention)
    if extra_terms:
        parts.extend(extra_terms)
    # Keep query readable and de-duplicated while preserving order.
    seen: set[str] = set()
    ordered: list[str] = []
    for token in parts:
        key = str(token).strip().lower()
        if key and key not in seen:
            seen.add(key)
            ordered.append(str(token))
    return " ".join(ordered)


def _is_low_soc(state: EnvironmentalState) -> bool:
    value = state.scalar("soil.organic_carbon_pct")
    try:
        return float(value) < 1.0
    except (TypeError, ValueError):
        return str(value).lower() in {"low", "very_low"}
