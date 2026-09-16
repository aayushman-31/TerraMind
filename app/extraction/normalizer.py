from __future__ import annotations

import json
import re
from typing import Any

from app.schemas.environment import EnvironmentalState, Observation

LAND_COVER_TAXONOMY = {
    "monoculture",
    "intercropping",
    "mixed cropping",
    "mixed_cropping",
    "agroforestry",
    "forest",
    "grassland",
    "wetland",
    "pasture",
    "cropland",
    "farm",
}

CROPPING_ALIASES = {
    "grow wheat continuously": "monoculture",
    "wheat continuously": "monoculture",
    "continuous wheat": "monoculture",
    "continuous wheat monoculture": "monoculture",
    "wheat monoculture": "monoculture",
    "continuous monoculture": "monoculture",
    "monoculture": "monoculture",
    "intercropped": "intercropping",
    "intercropping": "intercropping",
    "mixed cropping": "mixed_cropping",
    "rotated": "rotation",
    "crop rotation": "rotation",
    "agroforestry": "agroforestry",
}

CROPS = [
    "wheat",
    "rice",
    "maize",
    "corn",
    "barley",
    "millet",
    "sorghum",
    "soybean",
    "cotton",
    "sugarcane",
]


def observation(value: Any, unit: str | None = None, source: str = "user", confidence: str = "user_reported") -> Observation:
    return Observation(value=value, unit=unit, source=source, confidence=confidence)


def merge_structured(state: EnvironmentalState, payload: dict[str, Any], source: str = "structured_input") -> EnvironmentalState:
    def maybe_obs(raw: Any, unit: str | None = None) -> Observation | None:
        if raw is None:
            return None
        if isinstance(raw, dict) and "value" in raw:
            data = dict(raw)
            data.setdefault("source", source)
            data.setdefault("confidence", "structured_input")
            return Observation.model_validate(data)
        return observation(raw, unit=unit, source=source, confidence="structured_input")

    loc = payload.get("location") or {}
    soil = payload.get("soil") or {}
    land = payload.get("land") or {}
    bio = payload.get("biodiversity") or {}
    climate = payload.get("climate") or {}
    human = payload.get("human_impact") or {}

    mapping = [
        ("location.country", loc.get("country")),
        ("location.region", loc.get("region") or payload.get("region")),
        ("location.latitude", loc.get("latitude")),
        ("location.longitude", loc.get("longitude")),
        ("soil.ph", soil.get("ph")),
        ("soil.organic_carbon_pct", soil.get("organic_carbon_pct")),
        ("soil.moisture", soil.get("moisture")),
        ("land.land_use", land.get("land_use")),
        ("land.land_cover", land.get("land_cover")),
        ("land.crop", land.get("crop") or payload.get("crop")),
        ("land.cropping_system", land.get("cropping_system") or payload.get("cropping_system")),
        ("land.habitat_diversity", land.get("habitat_diversity")),
        ("land.fragmentation", land.get("fragmentation")),
        ("biodiversity.species_richness", bio.get("species_richness")),
        ("biodiversity.habitat_diversity", bio.get("habitat_diversity")),
        ("biodiversity.pollinator_presence", bio.get("pollinator_presence")),
        ("climate.temperature", climate.get("temperature")),
        ("climate.rainfall", climate.get("rainfall")),
        ("climate.rainfall_pattern", climate.get("rainfall_pattern")),
        ("human_impact.pollution", human.get("pollution")),
        ("human_impact.deforestation", human.get("deforestation")),
        ("human_impact.pesticide_use", human.get("pesticide_use")),
        ("human_impact.fertilizer_use", human.get("fertilizer_use")),
        ("human_impact.land_disturbance", human.get("land_disturbance")),
    ]
    units = {
        "soil.ph": "pH",
        "soil.organic_carbon_pct": "%",
        "location.latitude": "deg",
        "location.longitude": "deg",
    }
    for path, raw in mapping:
        obs = maybe_obs(raw, unit=units.get(path))
        if obs is not None:
            state.set_observation(path, obs)
    if payload.get("user_goal"):
        state.user_goal = maybe_obs(payload["user_goal"])
    return state


def extract_json_blob(message: str) -> dict[str, Any] | None:
    match = re.search(r"\{[\s\S]*\}", message)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None
