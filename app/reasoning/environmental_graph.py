from __future__ import annotations

from pathlib import Path

import yaml

from app.config.settings import get_settings
from app.schemas.environment import EnvironmentalState


def load_graph() -> dict:
    settings = get_settings()
    path = Path(settings.relationship_graph_path)
    if not path.is_file():
        path = Path(__file__).resolve().parents[2] / "config" / "environmental_graph.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class EnvironmentalGraph:
    def __init__(self) -> None:
        data = load_graph()
        self.nodes = {node["id"]: node for node in data["nodes"]}
        self.edges = data["edges"]
        self.adj: dict[str, list[dict]] = {}
        for edge in self.edges:
            self.adj.setdefault(edge["source"], []).append(edge)

    def pathways_from(self, start: str, max_depth: int = 6) -> list[list[str]]:
        paths: list[list[str]] = []

        def walk(node: str, trail: list[str]) -> None:
            if len(trail) >= max_depth or node not in self.adj:
                if len(trail) > 1:
                    paths.append(trail)
                return
            extended = False
            for edge in self.adj.get(node, []):
                nxt = edge["target"]
                if nxt in trail:
                    continue
                extended = True
                walk(nxt, trail + [nxt])
            if not extended and len(trail) > 1:
                paths.append(trail)

        walk(start, [start])
        return paths


def qualitative_pressure(state: EnvironmentalState, path: str) -> str | None:
    value = state.scalar(path)
    if value is None:
        return None
    if path == "soil.organic_carbon_pct":
        try:
            return "low" if float(value) < 1.0 else "adequate"
        except (TypeError, ValueError):
            return str(value)
    if path == "soil.ph":
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        if number >= 7.5:
            return "alkaline"
        if number <= 5.5:
            return "acidic"
        return "near_neutral"
    if path == "land.cropping_system":
        text = str(value).lower()
        if text in {"monoculture", "continuous_monoculture"}:
            return "simplified"
        return text
    return str(value)
