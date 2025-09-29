import pytest


@pytest.fixture
def assessment_req():
    return {
        "target_exam": "CBSE_Grade10_Physics_Monthly",
        "exam_type": "monthly",
        "subject": "Physics",
        "class": "10A",
        "previous_topics": [],
        "learning_gaps": [],
    }


def test_generate_assessment_enqueues(monkeypatch, client, assessment_req):
    async def fake_update_job_status(job_id, status):
        return None

    async def fake_process_job(self, params):
        return {"job_id": params["job_id"], "status": "completed", "result": {"questions": []}}

    monkeypatch.setattr(
        "core.services.db_operations.assessment_db.update_job_status",
        fake_update_job_status,
    )
    monkeypatch.setattr(
        "core.workers.assessment_worker.AssessmentWorker.process_assessment_job",
        fake_process_job,
    )

    r = client.post("/api/assessments/generate", json=assessment_req)
    assert r.status_code == 202
    body = r.json()
    assert "job_id" in body
    assert body["status"] == "pending"


def test_assessment_status_ok(monkeypatch, client):
    async def fake_get_by_job(job_id):
        return {"status": "completed", "_id": "A-1"}

    # Patch the symbol as imported into the controller module (not the source module)
    monkeypatch.setattr(
        "core.api.controllers.assessment_controller.get_assessment_by_job_id",
        fake_get_by_job,
    )
    r = client.get("/api/assessments/status/J-1")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"
    assert r.json()["assessment_id"] == "A-1"

