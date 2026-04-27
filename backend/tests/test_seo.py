def test_latest_seo(client):
    r = client.get("/api/seo/latest")
    assert r.status_code == 200
    body = r.json()
    assert "fecha" in body
    assert "mobile" in body
    assert "desktop" in body


def test_seo_history(client):
    r = client.get("/api/seo/history")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) >= 1


def test_seo_history_mobile_only(client):
    r = client.get("/api/seo/history?device=mobile")
    assert r.status_code == 200
    items = r.json()
    for item in items:
        assert "desktop" not in item


def test_seo_correlation_501(client):
    r = client.get("/api/seo/correlation")
    assert r.status_code == 501
