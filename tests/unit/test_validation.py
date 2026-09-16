from app.agent.policies import check_completeness
from app.extraction.parser import extract_from_text
from app.evidence.verifier import verify_recommendation
from app.schemas.responses import EvidenceItem, Recommendation


def test_clarification_when_incomplete():
    state = extract_from_text("Biodiversity is declining on my farm. I grow wheat and rainfall has been low.")
    result = check_completeness(state)
    assert result.complete is False
    assert "soil.organic_carbon_pct" in result.missing
    assert "land.cropping_system" in result.missing


def test_complete_after_core_variables():
    state = extract_from_text(
        "Biodiversity is declining. Wheat, low rainfall, organic carbon is 0.3%, pH is 7.8, continuous wheat monoculture."
    )
    result = check_completeness(state)
    assert result.complete is True


def test_verifier_strips_unsupported_percentages():
    rec = Recommendation(
        action="Intercrop",
        why_it_works="Intercropping will increase biodiversity by 37%.",
        metrics_impacted=["biodiversity.species_richness"],
        estimated_effect="37% increase",
        time_horizon="1 year",
        evidence=[
            EvidenceItem(
                document_id="x",
                title="Example",
                text="Diversification can improve biodiversity outcomes without a universal percentage.",
            )
        ],
        confidence="high",
        measurement_plan="observe",
    )
    verified = verify_recommendation(rec)
    assert "37%" not in verified.estimated_effect
    assert "cannot be estimated" in verified.estimated_effect.lower()
