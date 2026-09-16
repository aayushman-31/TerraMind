from __future__ import annotations

from app.reasoning.environmental_graph import EnvironmentalGraph, qualitative_pressure
from app.schemas.environment import EnvironmentalState
from app.schemas.responses import ReasoningTrace


class MultiMetricReasoner:
    def __init__(self) -> None:
        self.graph = EnvironmentalGraph()

    def reason(self, state: EnvironmentalState) -> ReasoningTrace:
        activated: list[str] = []
        constraints: list[str] = []
        pathways: list[list[str]] = []

        rainfall = qualitative_pressure(state, "climate.rainfall")
        if rainfall in {"low", "very_low", "drought"}:
            activated.append("climate.rainfall")
            constraints.append("Low rainfall implies water limitation, which constrains vegetation diversity and habitat persistence.")
            pathways.extend(self.graph.pathways_from("climate.rainfall")[:2])

        cropping = qualitative_pressure(state, "land.cropping_system")
        if cropping == "simplified":
            activated.append("land.cropping_system")
            constraints.append(
                "Wheat or other continuous monoculture reduces structural diversity and habitat heterogeneity."
            )
            pathways.extend(self.graph.pathways_from("land.cropping_system")[:2])

        soc = qualitative_pressure(state, "soil.organic_carbon_pct")
        if soc == "low":
            activated.append("soil.organic_carbon_pct")
            constraints.append(
                "Low soil organic carbon indicates degraded soil biological conditions and weaker ecosystem function."
            )
            pathways.extend(self.graph.pathways_from("soil.organic_carbon_pct")[:2])

        ph = qualitative_pressure(state, "soil.ph")
        if ph == "alkaline":
            activated.append("soil.ph")
            constraints.append("Alkaline soil can constrain some nutrient and biological processes.")

        if qualitative_pressure(state, "land.fragmentation") in {"high", "present"}:
            activated.append("land.fragmentation")
            constraints.append("Habitat fragmentation reduces habitat availability and species persistence.")
            pathways.extend(self.graph.pathways_from("land.fragmentation")[:1])

        if state.scalar("human_impact.deforestation") in {"present", "high", True}:
            activated.append("human_impact.deforestation")
            constraints.append("Deforestation increases fragmentation and removes habitat.")
            pathways.extend(self.graph.pathways_from("human_impact.deforestation")[:1])

        if state.scalar("human_impact.pollution") in {"present", "high", True}:
            activated.append("human_impact.pollution")
            constraints.append("Pollution is a direct pressure on species richness and sensitive taxa.")
            pathways.extend(self.graph.pathways_from("human_impact.pollution")[:1])

        if state.scalar("human_impact.pesticide_use") in {"high", "present"}:
            activated.append("human_impact.pesticide_use")
            constraints.append("Pesticide pressure can reduce pollinators and other non-target biodiversity.")

        crop = state.scalar("land.crop")
        if crop:
            activated.append("land.crop")
            constraints.append(f"Primary crop/land cover is {crop}.")

        notes = []
        if len({item.split(".")[0] for item in activated if "." in item}) >= 3 or len(activated) >= 3:
            notes.append("Multi-variable pressure: soil, water/climate, and land-use/habitat constraints should be addressed together.")
        else:
            notes.append("Fewer than three environmental pressures are fully specified; recommendations stay qualitative.")

        unique_paths = []
        seen = set()
        for path in pathways:
            key = tuple(path)
            if key not in seen:
                seen.add(key)
                unique_paths.append(path)

        return ReasoningTrace(
            activated_variables=list(dict.fromkeys(activated)),
            pathways=unique_paths[:8],
            constraints=constraints,
            notes=notes,
        )
