def test_timeline_experimental(client):
    r = client.get("/api/metrics/timeline/experimental?metric=visibility_rate")
    assert r.status_code == 200
    body = r.json()
    assert body["metric"] == "visibility_rate"
    assert len(body["points"]) >= 2


def test_timeline_experimental_invalid_metric(client):
    r = client.get("/api/metrics/timeline/experimental?metric=unknown_metric")
    assert r.status_code == 400


def test_timeline_live(client):
    r = client.get("/api/metrics/timeline/live?metric=engine_coverage_avg")
    assert r.status_code == 200
    body = r.json()
    assert len(body["points"]) >= 1


def test_timeline_live_engine(client):
    r = client.get("/api/metrics/timeline/live?metric=visibility_rate&engine=gemini")
    assert r.status_code == 200


def test_timeline_seo(client):
    r = client.get("/api/metrics/timeline/seo?device=mobile&metric=performance")
    assert r.status_code == 200
    body = r.json()
    assert len(body["points"]) >= 1


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
