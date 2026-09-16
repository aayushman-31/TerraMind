from app.extraction.normalizer import merge_structured
from app.schemas.environment import EnvironmentalState


def test_structured_json_merge():
    payload = {
        "soil": {"organic_carbon_pct": 0.3, "ph": 7.8},
        "climate": {"rainfall": "low"},
        "land": {"crop": "wheat", "cropping_system": "monoculture"},
        "location": {"region": "semi-arid"},
    }
    state = merge_structured(EnvironmentalState(), payload)
    assert state.scalar("soil.organic_carbon_pct") == 0.3
    assert state.scalar("soil.ph") == 7.8
    assert state.scalar("climate.rainfall") == "low"
    assert state.scalar("land.crop") == "wheat"
    assert state.soil.organic_carbon_pct.unit == "%"
