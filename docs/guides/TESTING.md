# Testing Guide

This project includes unit, API, integration, E2E, and migration tests. Use this guide to run suites, understand what each folder covers, and avoid common pitfalls.

## Quick commands

Run all tests

```bash
python -m pytest -q
```

Run by suite

```bash
# Unit tests
python -m pytest tests/unit -q

# API route tests
python -m pytest tests/api -q

# Integration tests
python -m pytest tests/integration -q

# End-to-end (requires running server at BASE)
python -m pytest tests/e2e -q

# Migration/legacy checks
python -m pytest tests/migration -q
```

Target a folder/file or filter by name

```bash
python -m pytest tests/unit/agents -q
python -m pytest tests/api/routes/test_assessment_routes.py -q
python -m pytest -k "content_agent or rag" -q
```

Exclude suites (e.g., skip e2e and migration)

```bash
python -m pytest -q -k "not e2e and not migration"
```

## Suite map (what lives where)

- tests/unit/
  - agents/: minimal async unit tests for Assessment, Content, Remedy agents
  - services/graphs/: graph build/import/state smoke tests (no real LLM calls)
  - services/helpers/: shared helper nodes, extraction and small DB helpers
- tests/api/
  - routes/: route behavior via FastAPI TestClient; DB calls monkeypatched
- tests/integration/
  - assessment/: assessment graph invocation and components
  - remedy/: Remedy→Content orchestration path and job state checks
  - rag/: RAG queries and orchestration (Pinecone may be required if not mocked)
- tests/e2e/
  - NCERT ingest + QA against a running server (BASE URL configurable)
- tests/migration/
  - legacy/migration shape and import checks

## Environment and server for E2E

- Start the API in another terminal (defaults to port 8080 unless set):

```bash
python main.py
```

- E2E tests target `BASE = ${NCERT_TEST_BASE:-http://127.0.0.1:8000/api}`.
  - To customize: set `NCERT_TEST_BASE` (e.g., PowerShell)

```powershell
$env:NCERT_TEST_BASE = "http://127.0.0.1:8000/api"
python -m pytest tests/e2e -q
```

- If the server isn't running, skip E2E: `-k "not e2e"`.

## Async tests and configuration

- Async tests are supported via `tests/conftest.py` without external plugins.
- Custom marker `@pytest.mark.asyncio` is declared in `pytest.ini` and optional.
- Pytest warning filters in `pytest.ini` hide noisy Pydantic v2 deprecations and tests returning values.

## What can break tests (common breakpoints)

- Patching the wrong symbol: patch where the function is imported/used.
  - Example for assessment status route:

```python
monkeypatch.setattr(
    "core.api.controllers.assessment_controller.get_assessment_by_job_id",
    fake_get_by_job,
)
```

- Live services not running: E2E uses httpx to call the server; start it or skip E2E.
- Pinecone not available: RAG integration tests may require Pinecone unless mocked; prefer running unit/API/integration subsets first.
- Non-deterministic LLM outputs: assert structure (keys/types), not exact text. Unit/integration tests should mock LLM layers.
- Event loop/Motor issues: DB calls in route/controller tests must be mocked to avoid real I/O.

## Typical warnings (and why)

- PytestReturnNotNoneWarning: a test returns a value instead of using asserts. We suppress this in `pytest.ini`; best practice is to replace returns with asserts.
- PydanticDeprecatedSince20: Pydantic v2 deprecation warnings; filtered in `pytest.ini`.

## Handy patterns

- Run a focused subset quickly:

```bash
python -m pytest tests/unit/agents -q
```

- Verify API smoke:

```bash
python -m pytest tests/api/routes -q
```

- Run integration (skip E2E):

```bash
python -m pytest tests/integration -q
```

## Troubleshooting

- Connection errors in E2E: ensure `NCERT_TEST_BASE` points to a live server (e.g., `http://127.0.0.1:8000/api`).
- Import errors after refactors: tests should use `core.*` imports; update any legacy `services.*`/`api.*` paths.
- Requirements file encoding (Windows): ensure `requirements.txt` is UTF-8 (no BOM) to avoid tooling issues.
