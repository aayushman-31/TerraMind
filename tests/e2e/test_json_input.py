def test_structured_json_input(client):
    response = client.post(
        "/api/v1/agent/query",
        json={
            "message": "Improve biodiversity on this farm.",
            "environment": {
                "location": {"region": "semi-arid"},
                "soil": {"organic_carbon_pct": 0.3, "ph": 7.8},
                "climate": {"rainfall": "low"},
                "land": {"crop": "wheat", "cropping_system": "monoculture"},
            },
        },
    )
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "recommendation_ready"
    assert data["environmental_state"]["soil"]["organic_carbon_pct"]["value"] == 0.3
    assert data["recommendations"]
    assert data["evidence"]
