def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "data_dir" in body


def test_config_target(client):
    r = client.get("/api/config/target")
    assert r.status_code == 200
    body = r.json()
    assert body["target_url"] == "https://programamos.es"
    assert body["target_brand"] == "Programamos"
    assert isinstance(body["engines_configured"], list)
