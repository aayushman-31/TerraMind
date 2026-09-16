from __future__ import annotations

from pathlib import Path

import yaml

from app.config.settings import get_settings
from app.schemas.environment import EnvironmentalState
from app.schemas.responses import EvidenceItem, ReasoningTrace, Recommendation


def load_interventions() -> list[dict]:
    settings = get_settings()
    path = Path(settings.interventions_path)
    if not path.is_file():
        path = Path(__file__).resolve().parents[2] / "config" / "interventions.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["interventions"]


def select_candidates(state: EnvironmentalState, reasoning: ReasoningTrace) -> list[dict]:
    interventions = load_interventions()
    activated = set(reasoning.activated_variables)
    rainfall = str(state.scalar("climate.rainfall") or "").lower()
    cropping = str(state.scalar("land.cropping_system") or "").lower()
    selected: list[dict] = []
    for item in interventions:
        when = item.get("applicable_when") or {}
        score = 0
        if rainfall in {"low", "very_low", "drought"} and item["id"] in {
            "drought_compatible_intercropping",
            "cover_crops",
            "agroforestry",
        }:
            score += 2
        if cropping in {"monoculture", "continuous_monoculture"} and item["id"] in {
            "drought_compatible_intercropping",
            "habitat_strips",
            "cover_crops",
        }:
            score += 2
        if "soil.organic_carbon_pct" in activated and item["id"] in {
            "cover_crops",
            "reduced_disturbance",
            "drought_compatible_intercropping",
            "agroforestry",
        }:
            score += 2
        if "human_impact.pollution" in activated and item["id"] == "pollution_and_pesticide_reduction":
            score += 4
        if "human_impact.deforestation" in activated or "land.fragmentation" in activated:
            if item["id"] in {"forest_connectivity", "habitat_strips", "agroforestry"}:
                score += 3
        if "human_impact.pesticide_use" in activated and item["id"] == "pollution_and_pesticide_reduction":
            score += 3
        # Prefer interventions that touch multiple activated nodes.
        overlap = len(set(item.get("addresses") or []) & (activated | set(reasoning.notes)))
        score += overlap
        if when.get("cropping_systems") and cropping and cropping not in when["cropping_systems"]:
            if cropping:
                score -= 1
        if score > 0:
            selected.append({**item, "_score": score})
    selected.sort(key=lambda item: item["_score"], reverse=True)
    if not selected:
        selected = [{**item, "_score": 1} for item in interventions[:2]]
    return selected[:4]


def evidence_for_intervention(intervention: dict, evidence: list[EvidenceItem]) -> list[EvidenceItem]:
    terms = [term.lower() for term in intervention.get("search_terms") or []]
    terms.extend(str(m).replace(".", " ").lower() for m in intervention.get("metrics_impacted") or [])
    ranked: list[tuple[int, EvidenceItem]] = []
    for item in evidence:
        blob = f"{item.title} {item.text}".lower()
        hits = sum(1 for term in terms if term.split()[0] in blob or term in blob)
        ranked.append((hits, item))
    ranked.sort(key=lambda pair: (pair[0], pair[1].score or 0), reverse=True)
    chosen = [item for hits, item in ranked if hits > 0][:3]
    if not chosen:
        chosen = evidence[:2]
    return chosen


def build_recommendations(
    state: EnvironmentalState,
    reasoning: ReasoningTrace,
    evidence: list[EvidenceItem],
) -> list[Recommendation]:
    recs: list[Recommendation] = []
    for intervention in select_candidates(state, reasoning):
        linked = evidence_for_intervention(intervention, evidence)
        time = intervention.get("time_horizon") or {}
        if isinstance(time, dict):
            time_text = "; ".join(f"{k}: {v}" for k, v in time.items())
        else:
            time_text = str(time)
        why = (
            " ".join(reasoning.constraints[:3])
            + " This intervention can act on several of those nodes at once rather than treating a single variable."
        )
        recs.append(
            Recommendation(
                action=intervention["action"],
                why_it_works=why,
                metrics_impacted=list(intervention.get("metrics_impacted") or []),
                expected_direction=dict(intervention.get("expected_direction") or {}),
                estimated_effect=(
                    "Available evidence indicates a plausible qualitative benefit for the listed metrics, "
                    "but a reliable percentage improvement cannot be estimated for this site from the retrieved sources."
                ),
                time_horizon=time_text,
                evidence=linked,
                confidence="moderate" if linked else "low",
                assumptions=[
                    "No severe contamination beyond what was described.",
                    "Selected species or practices are adapted to local rainfall.",
                ],
                tradeoffs=list(intervention.get("tradeoffs") or []),
                measurement_plan=(
                    "Measure soil organic carbon annually; record vegetation/habitat diversity; "
                    "log species or pollinator observations; monitor soil moisture relative to rainfall."
                ),
                internal_rank=float(intervention.get("_score") or 0),
            )
        )
    return recs
