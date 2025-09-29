def test_root_ok(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json().get("message") == "API is running!"


def test_rag_status_works(monkeypatch, client):
    async def fake_status():
        return {"stage": "idle", "files_processed": 0}

    monkeypatch.setattr(
        "core.api.controllers.rag_controller.get_ingest_status",
        fake_status,
    )
    r = client.get("/api/rag/ncert/status")
    assert r.status_code == 200
    assert r.json()["stage"] == "idle"


def test_content_debug_jobs_isolated(monkeypatch, client):
    async def fake_get_debug_jobs():
        return {"regular_jobs": {}, "integrated_reedy_jobs": {}}

    # Note: intentional small diff in key to ensure we assert structure, not identity
    monkeypatch.setattr(
        "core.api.controllers.content_controller.ContentController.get_debug_jobs",
        fake_get_debug_jobs,
    )
    r = client.get("/api/v1/debug/jobs")
    assert r.status_code == 200
    data = r.json()
    assert "regular_jobs" in data

