import os
import json

import httpx

BASE = os.getenv("NCERT_TEST_BASE", "http://127.0.0.1:8000/api")


def test_ingest_subset():
    path = os.getenv("NCERT_TEST_PDF", "CBSE/grade_10/ch (1).pdf")
    with httpx.Client(timeout=60.0) as c:
        r = c.post(f"{BASE}/rag/ncert/ingest", json={"paths": [path]})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["processed_files"] >= 1
        assert data["total_chunks"] >= 1


def test_status_and_qa():
    with httpx.Client(timeout=30.0) as c:
        s = c.get(f"{BASE}/rag/ncert/status")
        assert s.status_code == 200
        status = s.json()
        # Upsert may be async-fast; allow zero but log
        assert status["processed_files"] >= 1

        q = c.post(f"{BASE}/rag/ncert/qa", json={
            "query": "Define work and energy",
            "grade": "grade_10",
            "top_k": 5
        })
        assert q.status_code == 200, q.text
        res = q.json()
        assert "citations" in res

