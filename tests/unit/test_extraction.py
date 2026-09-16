from app.extraction.parser import extract_from_text


def test_extract_demo_sentence():
    text = (
        "My farm is in a semi-arid region. I grow wheat continuously. "
        "The soil has 0.3% organic carbon and rainfall has been very low."
    )
    state = extract_from_text(text)
    assert state.scalar("location.region") == "semi-arid"
    assert state.scalar("land.crop") == "wheat"
    assert state.scalar("land.cropping_system") == "monoculture"
    assert state.scalar("soil.organic_carbon_pct") == 0.3
    assert state.scalar("climate.rainfall") in {"low", "very_low"}


def test_extract_ph_and_monoculture():
    state = extract_from_text("Organic carbon is 0.3%, pH is 7.8, and it is continuous wheat monoculture.")
    assert state.scalar("soil.organic_carbon_pct") == 0.3
    assert state.scalar("soil.ph") == 7.8
    assert state.scalar("land.crop") == "wheat"
    assert state.scalar("land.cropping_system") == "monoculture"
