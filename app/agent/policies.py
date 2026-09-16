from __future__ import annotations

from dataclasses import dataclass

from app.schemas.environment import EnvironmentalState

HIGH_VALUE_FOR_BIODIVERSITY = [
    "soil.organic_carbon_pct",
    "climate.rainfall",
    "land.cropping_system",
    "land.crop",
    "soil.moisture",
    "land.habitat_diversity",
    "human_impact.pollution",
    "human_impact.deforestation",
]

QUESTION_BANK = {
    "soil.organic_carbon_pct": "What is the approximate soil organic carbon (%)?",
    "climate.rainfall": "Is rainfall best described as low, moderate, or high, and has drought been occurring?",
    "land.cropping_system": "Is the crop grown as a continuous monoculture or rotated/intercropped with other crops?",
    "land.crop": "What is the main crop or land cover?",
    "soil.ph": "What is the soil pH?",
    "soil.moisture": "What is the soil moisture condition (dry/low, moderate, or wet)?",
    "land.habitat_diversity": "Does the field border natural vegetation, habitat strips, or trees?",
    "human_impact.pollution": "Is pollution or heavy pesticide use a known pressure on the site?",
    "human_impact.deforestation": "Has nearby forest or native habitat been cleared or fragmented?",
}


@dataclass
class CompletenessResult:
    complete: bool
    missing: list[str]
    questions: list[str]
    rationale: str


def _known(state: EnvironmentalState, path: str) -> bool:
    return state.get_observation(path) is not None


def check_completeness(state: EnvironmentalState) -> CompletenessResult:
    """Ask only high-value questions needed for a defensible recommendation."""
    known = state.known_paths()
    goal = str(state.user_goal.value).lower() if state.user_goal else "improve biodiversity"

    needed: list[str] = []
    if "pollution" in " ".join(str(v.value).lower() for v in known.values()) or "pollution" in goal:
        needed = ["human_impact.pollution", "biodiversity.species_richness", "human_impact.land_disturbance"]
    if any(
        token in " ".join(str(v.value).lower() for v in known.values())
        for token in ["deforest", "fragment"]
    ) or _known(state, "human_impact.deforestation"):
        needed = [
            "human_impact.deforestation",
            "land.fragmentation",
            "climate.rainfall",
            "biodiversity.habitat_diversity",
        ]

    # Default farm-biodiversity pathway: soil + water + land-use together.
    if not needed:
        needed = [
            "climate.rainfall",
            "land.crop",
            "land.cropping_system",
            "soil.organic_carbon_pct",
        ]

    # If two of the three core farm variables exist, ask the remaining plus one discriminator.
    core = ["climate.rainfall", "land.cropping_system", "soil.organic_carbon_pct"]
    core_known = sum(_known(state, path) for path in core)

    missing = [path for path in needed if not _known(state, path)]

    # Never ask everything. Cap at 3 high-value questions.
    if core_known >= 2 and "soil.ph" not in missing and not _known(state, "soil.ph"):
        if len(missing) < 3:
            missing.append("soil.ph")
    if _known(state, "climate.rainfall") and not _known(state, "soil.moisture"):
        if "soil.moisture" not in missing and len(missing) < 3:
            missing.append("soil.moisture")

    # Sufficient for recommendation if at least 3 distinct domains are populated
    # and at least 2 of the core farm variables (or pollution/deforestation triples).
    domains = {path.split(".")[0] for path in known if "." in path}
    if _known(state, "human_impact.pollution") and _known(state, "biodiversity.species_richness"):
        complete = True
        missing = []
    elif _known(state, "human_impact.deforestation") and (
        _known(state, "land.fragmentation") or _known(state, "climate.rainfall")
    ):
        complete = len(domains) >= 2
        if complete:
            missing = []
    else:
        complete = core_known >= 3 or (core_known >= 2 and len(domains) >= 3 and len(missing) == 0)
        if core_known >= 3:
            complete = True
            missing = []
        elif core_known == 2 and _known(state, "land.crop"):
            # Spec demo: rainfall + crop + missing SOC/pH/cropping should still clarify.
            complete = core_known >= 3
        elif core_known >= 2 and _known(state, "land.crop") and _known(state, "soil.organic_carbon_pct"):
            complete = True
            missing = []

    # Explicit demo path: wheat + low rainfall without SOC/cropping/pH should clarify.
    if (
        _known(state, "land.crop")
        and _known(state, "climate.rainfall")
        and not _known(state, "soil.organic_carbon_pct")
        and not _known(state, "land.cropping_system")
    ):
        complete = False
        missing = ["soil.organic_carbon_pct", "soil.ph", "land.cropping_system"]

    missing = missing[:3]
    questions = [QUESTION_BANK.get(path, f"Can you provide {path}?") for path in missing]
    rationale = (
        "Enough multi-variable context is available."
        if complete
        else "High-value gaps remain for distinguishing soil degradation, water limitation, and habitat simplification."
    )
    return CompletenessResult(complete=complete, missing=missing, questions=questions, rationale=rationale)
