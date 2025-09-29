import pytest


@pytest.fixture
def ahs_payload():
    return {
        "teacher_class_id": "TC-1",
        "session_id": "S-1",
        "duration_minutes": 15,
        "grade_level": "grade_10",
        "curriculum_goal": "vectors",
        "topic": "dot product",
        "context_refs": {},
        "modes": ["learn_by_reading", "learn_by_solving"],
    }


def test_create_ahs_job(monkeypatch, client, ahs_payload):
    class FakeJob:
        def __init__(self):
            self.job_id = "JOB_AHS_abc123"
            self.status = "pending"
            self.progress = 0
            self.error = None
            self.result_doc_id = None

        def dict(self):
            return {
                "job_id": self.job_id,
                "status": self.status,
                "progress": self.progress,
                "error": self.error,
                "result_doc_id": self.result_doc_id,
            }

    async def fake_controller(payload):
        return FakeJob()

    monkeypatch.setattr(
        "core.api.controllers.content_controller.ContentController.create_ahs_content",
        fake_controller,
    )
    r = client.post("/api/v1/contentGenerationForAHS", json=ahs_payload)
    assert r.status_code == 202
    body = r.json()
    assert body["job_id"].startswith("JOB_AHS_")
    assert body["status"] in ("pending", "in_progress", "completed", "failed")


def test_job_status_completed(monkeypatch, client):
    class FakeJob:
        def __init__(self):
            self.job_id = "JOB_REM_abc123"
            self.status = "completed"
            self.progress = 100
            self.error = None
            self.result_doc_id = "student_reports/xyz"

    async def fake_status(job_id):
        return FakeJob()

    monkeypatch.setattr(
        "core.api.controllers.content_controller.ContentController.get_job_status",
        fake_status,
    )
    r = client.get("/api/v1/jobs/JOB_REM_abc123")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"

