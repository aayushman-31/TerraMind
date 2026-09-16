from __future__ import annotations

import copy

from app.schemas.environment import EnvironmentalState, Observation


def merge_states(base: EnvironmentalState, incoming: EnvironmentalState) -> EnvironmentalState:
    merged = EnvironmentalState.model_validate(copy.deepcopy(base.model_dump()))
    for path, obs in incoming.known_paths().items():
        existing = merged.get_observation(path)
        if existing is None or obs.source in {"user", "structured_input"}:
            merged.set_observation(path, Observation.model_validate(obs.model_dump()))
    if incoming.user_goal is not None:
        merged.user_goal = incoming.user_goal
    return merged
