def test_conflicting_evidence_is_explained(client):
    response = client.post(
        "/api/v1/agent/query",
        json={
            "message": "Semi-arid wheat farm, low rainfall, 0.3% organic carbon, continuous monoculture. Should I use cover crops given conflicting dryland water results?",
            "environment": {
                "location": {"region": "semi-arid"},
                "soil": {"organic_carbon_pct": 0.3, "ph": 7.8},
                "climate": {"rainfall": "low"},
                "land": {"crop": "wheat", "cropping_system": "monoculture"},
            },
        },
    )
    data = response.json()
    assert data["status"] == "recommendation_ready"
    blob = (data.get("message") or "").lower()
    blob += " ".join(rec["estimated_effect"].lower() for rec in data["recommendations"])
    assert "mixed" in blob or "study a" in blob or "cannot be estimated" in blob
