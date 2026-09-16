def test_hybrid_search_endpoint(client):
    response = client.post(
        "/api/v1/knowledge/search",
        json={"query": "soil organic carbon biodiversity agriculture", "top_k": 5, "filters": {"domain": "soil"}},
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert results
    assert "organic" in results[0]["text"].lower() or "soil" in results[0]["title"].lower()
    assert results[0]["document_id"]
    assert results[0]["title"]
