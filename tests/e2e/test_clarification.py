def test_clarification_flow(client):
    response = client.post(
        "/api/v1/agent/query",
        json={"message": "Biodiversity is declining on my farm. I grow wheat and rainfall has been low."},
    )
    data = response.json()
    assert data["status"] == "clarification_required"
    assert data["missing_information"]
    assert "organic carbon" in data["message"].lower() or "soil.organic_carbon_pct" in data["missing_information"]
