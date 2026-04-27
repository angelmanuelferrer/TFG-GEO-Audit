def test_coverage_matrix(client):
    r = client.get("/api/metrics/coverage-matrix?run_id=LIVE-2026-W14")
    assert r.status_code == 200
    body = r.json()
    assert "matrix" in body
    assert "informacional" in body["matrix"] or len(body["matrix"]) > 0


def test_sentiment_distribution(client):
    r = client.get("/api/metrics/sentiment-distribution?run_id=LIVE-2026-W14")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    engines = [item["engine"] for item in body]
    assert "gemini" in engines


def test_brand_mentions_experimental(client):
    r = client.get("/api/metrics/brand-mentions?run_id=run_20260405_173413")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 0
