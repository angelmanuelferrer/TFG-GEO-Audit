def test_dashboard_overview(client):
    r = client.get("/api/dashboard/overview")
    assert r.status_code == 200
    body = r.json()

    assert "target" in body
    assert body["target"]["url"] == "https://programamos.es"

    assert "experimental" in body
    exp = body["experimental"]
    assert exp["run_id"] == "run_20260405_173413"
    assert exp["visibility_rate"] > 0
    assert "delta_vs_previous" in exp

    assert "live" in body
    live = body["live"]
    assert live["latest_run_id"].startswith("LIVE-")
    assert "by_engine" in live

    assert "seo" in body
    seo = body["seo"]
    assert "mobile" in seo
    assert "desktop" in seo

    assert "alerts" in body
