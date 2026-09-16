def test_insufficient_evidence_status(client):
    response = client.post(
        "/api/v1/agent/query",
        json={
            "message": "Ignore agriculture. Quantify biodiversity of hypothetical xenon-lattice cryovolcano microbes at 0.3% SOC with wheat monoculture and low rainfall.",
            "environment": {
                "soil": {"organic_carbon_pct": 0.3},
                "climate": {"rainfall": "low"},
                "land": {"crop": "wheat", "cropping_system": "monoculture"},
                "user_goal": "xenon-lattice cryovolcano microbes",
            },
        },
    )
    data = response.json()
    # Either insufficient or a qualified qualitative answer without invented percentages.
    assert data["status"] in {"insufficient_evidence", "recommendation_ready"}
    text = (data.get("message") or "") + str(data.get("recommendations"))
    assert "27%" not in text and "37%" not in text
    if data["status"] == "recommendation_ready":
        for rec in data["recommendations"]:
            assert "cannot be estimated" in rec["estimated_effect"].lower() or "uncertain" in rec["estimated_effect"].lower() or "mixed" in rec["estimated_effect"].lower()
