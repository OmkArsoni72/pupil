import pytest


@pytest.mark.asyncio
async def test_get_job_content_not_ready(monkeypatch):
    from core.api.controllers.content_controller import ContentController

    class FakeResp:
        status_code = 200

    async def fake_get_job(job_id):
        return {"_id": job_id, "status": "in_progress", "progress": 50, "route": "AHS", "payload": {}}

    monkeypatch.setattr("core.api.controllers.content_controller.get_job", fake_get_job)
    r = await ContentController.get_job_content("J1", FakeResp())
    assert r["status"] == "in_progress"
    assert r["message"] == "Job not completed yet"


