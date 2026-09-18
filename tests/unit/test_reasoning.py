from app.extraction.normalizer import merge_structured
from app.reasoning.multi_metric import MultiMetricReasoner
from app.schemas.environment import EnvironmentalState


def test_multi_variable_pathways():
    state = merge_structured(
        EnvironmentalState(),
        {
            "soil": {"organic_carbon_pct": 0.3},
            "climate": {"rainfall": "low"},
            "land": {"crop": "wheat", "cropping_system": "monoculture"},
        },
    )
    trace = MultiMetricReasoner().reason(state)
    assert "soil.organic_carbon_pct" in trace.activated_variables
    assert "climate.rainfall" in trace.activated_variables
    assert "land.cropping_system" in trace.activated_variables
    assert any("water" in c.lower() or "rainfall" in c.lower() for c in trace.constraints)
    assert any("monoculture" in c.lower() or "heterogeneity" in c.lower() for c in trace.constraints)
    assert any("organic carbon" in c.lower() for c in trace.constraints)
    assert len(trace.pathways) >= 2
