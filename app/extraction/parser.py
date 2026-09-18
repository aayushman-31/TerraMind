from __future__ import annotations

import re
from typing import Any

from app.extraction.normalizer import CROPPING_ALIASES, CROPS, observation
from app.schemas.environment import EnvironmentalState

SOC_RE = re.compile(
    r"(?:soil\s+)?(?:organic\s+carbon|soc)\s*(?:is|=|:|of)?\s*([0-9]*\.?[0-9]+)\s*%?",
    re.I,
)
SOC_ALT_RE = re.compile(r"([0-9]*\.?[0-9]+)\s*%\s*(?:soil\s+)?organic\s+carbon", re.I)
PH_RE = re.compile(r"\bpH\s*(?:is|=|:)?\s*([0-9]*\.?[0-9]+)", re.I)
LATLON_RE = re.compile(r"(-?\d{1,3}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)")


def _set(state: EnvironmentalState, path: str, value: Any, unit: str | None = None, confidence: str = "user_reported") -> None:
    state.set_observation(path, observation(value, unit=unit, confidence=confidence))


def extract_from_text(message: str, state: EnvironmentalState | None = None) -> EnvironmentalState:
    state = state or EnvironmentalState()
    text = message.strip()
    lowered = text.lower()

    if any(term in lowered for term in ["biodiversity", "species richness", "pollinator"]):
        if state.user_goal is None:
            state.user_goal = observation("improve biodiversity", confidence="inferred")

    soc = SOC_RE.search(text) or SOC_ALT_RE.search(text)
    if soc:
        _set(state, "soil.organic_carbon_pct", float(soc.group(1)), unit="%")

    ph = PH_RE.search(text)
    if ph:
        _set(state, "soil.ph", float(ph.group(1)), unit="pH")

    coords = LATLON_RE.search(text)
    if coords:
        _set(state, "location.latitude", float(coords.group(1)), unit="deg")
        _set(state, "location.longitude", float(coords.group(2)), unit="deg")

    for alias, canonical in sorted(CROPPING_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if alias in lowered:
            _set(state, "land.cropping_system", canonical)
            break
    if state.scalar("land.cropping_system") is None and re.search(
        r"grow \w+ continuou|continuou\w* (wheat|crop|monoculture)|wheat.*continuou",
        lowered,
    ):
        _set(state, "land.cropping_system", "monoculture")

    for crop in CROPS:
        if re.search(rf"\b{crop}\b", lowered):
            _set(state, "land.crop", "maize" if crop == "corn" else crop)
            break

    if "semi-arid" in lowered or "semiarid" in lowered:
        _set(state, "location.region", "semi-arid")
    rajasthan = re.search(r"\brajasthan\b", lowered)
    if rajasthan:
        _set(state, "location.region", "Rajasthan")
        _set(state, "location.country", "India", confidence="inferred")

    if re.search(r"\b(very low|low) rainfall\b|rainfall (has been |is )?(very low|low)|drought", lowered):
        value = "very_low" if "very low" in lowered or "drought" in lowered else "low"
        _set(state, "climate.rainfall", value)
        if "drought" in lowered:
            _set(state, "climate.drought_condition", "present")
    elif re.search(r"\bhigh rainfall\b|rainfall (is |has been )?high", lowered):
        _set(state, "climate.rainfall", "high")

    if re.search(r"\bsoil moisture\b", lowered):
        if "low" in lowered or "dry" in lowered:
            _set(state, "soil.moisture", "low")
        elif "high" in lowered:
            _set(state, "soil.moisture", "high")
    elif "dry" in lowered and state.scalar("soil.moisture") is None:
        _set(state, "soil.moisture", "low", confidence="inferred")

    if "deforestation" in lowered or "forest cleared" in lowered or "forest loss" in lowered:
        _set(state, "human_impact.deforestation", "present")
    if "fragment" in lowered:
        _set(state, "land.fragmentation", "high")
    if "pollution" in lowered or "polluted" in lowered:
        _set(state, "human_impact.pollution", "present")
    if "pesticide" in lowered:
        _set(state, "human_impact.pesticide_use", "high")
    if "fertilizer" in lowered:
        _set(state, "human_impact.fertilizer_use", "present")
    if re.search(r"till|disturbance|plough|plow", lowered):
        _set(state, "human_impact.land_disturbance", "high")

    if "species richness" in lowered and re.search(r"low|declin", lowered):
        _set(state, "biodiversity.species_richness", "low")
    if "habitat diversity" in lowered and re.search(r"low|declin", lowered):
        _set(state, "biodiversity.habitat_diversity", "low")
    if "pollinator" in lowered and re.search(r"absent|declin|low", lowered):
        _set(state, "biodiversity.pollinator_presence", "low")

    if any(word in lowered for word in ["farm", "field", "crop", "wheat", "agriculture"]):
        if state.scalar("land.land_use") is None:
            _set(state, "land.land_use", "agriculture", confidence="inferred")
            _set(state, "land.land_cover", "cropland", confidence="inferred")

    return state
