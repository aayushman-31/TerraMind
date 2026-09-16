def test_multi_turn_memory(client):
    sid = client.post("/api/v1/session", json={}).json()["session_id"]
    client.post("/api/v1/agent/query", json={"session_id": sid, "message": "My farm is in Rajasthan."})
    client.post("/api/v1/agent/query", json={"session_id": sid, "message": "Wheat."})
    client.post("/api/v1/agent/query", json={"session_id": sid, "message": "Rainfall is very low."})
    stored = client.get(f"/api/v1/session/{sid}").json()
    state = stored["environmental_state"]
    assert state["location"]["region"]["value"] in {"Rajasthan", "rajasthan"}
    assert state["land"]["crop"]["value"] == "wheat"
    assert state["climate"]["rainfall"]["value"] in {"low", "very_low"}
