def test_complete_demo_case(client):
    created = client.post("/api/v1/session", json={}).json()
    sid = created["session_id"]
    first = client.post(
        "/api/v1/agent/query",
        json={
            "session_id": sid,
            "message": "Biodiversity is declining on my farm. I grow wheat and rainfall has been low.",
        },
    )
    assert first.status_code == 200
    body = first.json()
    assert body["status"] == "clarification_required"

    second = client.post(
        "/api/v1/agent/query",
        json={
            "session_id": sid,
            "message": "Organic carbon is 0.3%, pH is 7.8, and it is continuous wheat monoculture.",
        },
    )
    data = second.json()
    assert data["status"] == "recommendation_ready"
    assert len(data["recommendations"]) >= 1
    rec = data["recommendations"][0]
    assert rec["metrics_impacted"]
    assert rec["time_horizon"]
    assert rec["evidence"]
    assert "37%" not in data["message"]
    reasoning = data["reasoning"]
    activated = reasoning["activated_variables"]
    assert "soil.organic_carbon_pct" in activated
    assert "climate.rainfall" in activated
    assert "land.cropping_system" in activated
    joined = " ".join(rec["action"] for rec in data["recommendations"]).lower()
    assert "intercrop" in joined or "cover" in joined or "agroforest" in joined or "habitat" in joined
