from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

Confidence = Literal[
    "user_reported",
    "inferred",
    "structured_input",
    "unknown",
    "low",
    "moderate",
    "high",
]


class Observation(BaseModel):
    value: Any
    unit: str | None = None
    source: str = "user"
    date: str | None = None
    confidence: str = "user_reported"


class LocationState(BaseModel):
    country: Observation | None = None
    region: Observation | None = None
    latitude: Observation | None = None
    longitude: Observation | None = None


class SoilState(BaseModel):
    ph: Observation | None = None
    organic_carbon_pct: Observation | None = None
    moisture: Observation | None = None


class LandState(BaseModel):
    land_use: Observation | None = None
    land_cover: Observation | None = None
    crop: Observation | None = None
    cropping_system: Observation | None = None
    habitat_diversity: Observation | None = None
    fragmentation: Observation | None = None


class BiodiversityState(BaseModel):
    species_richness: Observation | None = None
    habitat_diversity: Observation | None = None
    pollinator_presence: Observation | None = None
    native_species_presence: Observation | None = None


class ClimateState(BaseModel):
    temperature: Observation | None = None
    rainfall: Observation | None = None
    rainfall_pattern: Observation | None = None
    seasonality: Observation | None = None
    drought_condition: Observation | None = None


class HumanImpactState(BaseModel):
    pollution: Observation | None = None
    deforestation: Observation | None = None
    pesticide_use: Observation | None = None
    fertilizer_use: Observation | None = None
    land_disturbance: Observation | None = None


class EnvironmentalState(BaseModel):
    location: LocationState = Field(default_factory=LocationState)
    soil: SoilState = Field(default_factory=SoilState)
    land: LandState = Field(default_factory=LandState)
    biodiversity: BiodiversityState = Field(default_factory=BiodiversityState)
    climate: ClimateState = Field(default_factory=ClimateState)
    human_impact: HumanImpactState = Field(default_factory=HumanImpactState)
    user_goal: Observation | None = None
    data_provenance: dict[str, Any] = Field(default_factory=dict)
    updated_at: str | None = None

    def set_observation(self, path: str, observation: Observation) -> None:
        if path == "user_goal":
            self.user_goal = observation
            return
        section, field = path.split(".", 1)
        target = getattr(self, section)
        setattr(target, field, observation)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def get_observation(self, path: str) -> Observation | None:
        if path == "user_goal":
            return self.user_goal
        section, field = path.split(".", 1)
        target = getattr(self, section)
        return getattr(target, field)

    def known_paths(self) -> dict[str, Observation]:
        known: dict[str, Observation] = {}
        mapping = {
            "location": self.location,
            "soil": self.soil,
            "land": self.land,
            "biodiversity": self.biodiversity,
            "climate": self.climate,
            "human_impact": self.human_impact,
        }
        for section, model in mapping.items():
            for field_name, value in model.model_dump().items():
                if value is not None:
                    known[f"{section}.{field_name}"] = Observation.model_validate(value)
        if self.user_goal is not None:
            known["user_goal"] = self.user_goal
        return known

    def scalar(self, path: str) -> Any:
        obs = self.get_observation(path)
        return None if obs is None else obs.value
