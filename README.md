   # PupilPrep Backend

Welcome to the PupilPrep backend. This repository powers the educator (PupilTeach) and student (PupilLearn) experiences with APIs, AI pipelines, RAG retrieval, real-time interactions, and orchestration for remediation flows.

If you're new, start here:

- docs/DEVELOPER_ONBOARDING.md — high-level orientation to the codebase and flows

---

## Architecture Overview

PupilPrep comprises:

- PupilTeach (educator web app)
- PupilLearn (student app, mobile-first oriented)
- Backend & AI Engine (this repo): APIs, business logic, persistence, RAG, embeddings, and real-time updates

Feedback loop: teacher delivers → student interacts → engine analyzes → insights to teacher and adaptive support to student.

Key backend layers (see `core/`):

- `api/` — routes, controllers, and request/response schemas
- `services/` — business logic and integrations (RAG, embeddings, Pinecone, etc.)
- `agents/`, `graphs/`, `nodes/` — orchestration of multi-step AI workflows
- `models/` — domain models and data structures
- `workers/` — background tasks

Documentation index:

- `docs/prd/` — product specs and flows
- `docs/migration/` — migration notes and refactors
- `docs/REMEDY_AGENT_README.md` — remedy agent overview
- `docs/prd/RAG_SYSTEM_DOCUMENTATION.md` — RAG design

---

## Getting Started

1. Python env

- Create a virtual environment (Python per `requirements.txt`).

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Configure environment

- Check `scripts/debug_env.py` for required environment variables.
- Create a `.env` (or equivalent) with API keys, DB, vector store config.

4. Run the backend

```bash
python main.py
```

5. Run tests

```bash
python scripts/run_tests.py
```

Helpful scripts: `scripts/quick_setup.py`, `scripts/quick_test_pipeline.py`, `scripts/demo_rag_system.py`.

---

## Repository Layout

```
core/
  api/
    controllers/  # request handlers
    routes/       # route registration
    schemas/      # validation models
  agents/         # orchestration of AI workflows
  graphs/         # graph-based pipelines
  models/         # domain models
  nodes/          # modular processing units
  services/       # business logic, RAG, embeddings, integrations
  workers/        # background jobs
docs/             # product and technical docs
scripts/          # setup, ingestion, debug, and demo scripts
tests/            # test suite (integration and feature flows)
```

---

## Core Flows (What to Read First)

- RAG ingestion and retrieval:

  - Docs: `docs/prd/RAG_SYSTEM_DOCUMENTATION.md`, `docs/prd/RAG_INTEGRATION_README.md`, `docs/prd/RAG_IMPLEMENTATION_SUMMARY.md`
  - Scripts: `scripts/deploy_rag_system.py`, `scripts/setup_rag.py`, `scripts/populate_vectors.py`

- Remedy logic (Adaptive Remedy Loop):

  - Docs: `docs/REMEDY_AGENT_README.md`, `docs/prd/remedy_Agent.md`, `docs/prd/whole_flow_mermaid.md`
  - Code: `core/agents/`, `core/graphs/`, `core/nodes/`, `core/services/`

- API surface:
  - `core/api/routes/`, `core/api/controllers/`, `core/api/schemas/`

---

## Running End-to-End Demos

- Quick pipeline test:

```bash
python scripts/quick_test_pipeline.py
```

- Demo RAG system:

```bash
python scripts/demo_rag_system.py
```

- Deploy/Populate vectors:

```bash
python scripts/deploy_rag_system.py
python scripts/populate_vectors.py
```

---

## Vector Store and Embeddings (Pinecone, etc.)

- Ingestion scripts create embeddings and upsert to the configured vector store.
- Retrieval is used across content generation, question answering, and remediation.
- See `scripts/populate_pinecone_indexes.py`, `scripts/populate_vectors.py`, and services under `core/services/`.

Installation note: for Pinecone SDK use the official package name.

```bash
pip install pinecone
```

---

## Testing

Run the whole suite:

```bash
python scripts/run_tests.py
```

Detailed testing guide (commands, suites, breakpoints, warnings):

- docs/guides/TESTING.md

Good entry tests:

- `tests/test_rag_system.py`
- `tests/test_rag_integration.py`
- `tests/test_ncert_ingest_and_query.py`
- `tests/test_remedy_agent.py`
- `tests/test_integrated_remedy.py`

---

## Troubleshooting

- Use `scripts/debug_env.py` to verify env vars.
- Check `scripts/check_pinecone_status.py` if vector services fail.
- For route/content issues: `scripts/debug_content_route.py` and related migration docs in `docs/migration/`.

---

## Contributing

- Keep controllers thin; put business logic in `services/` or `nodes/`.
- Add/extend tests for new flows.
- Update docs under `docs/` when behavior changes.

---

## License

Proprietary — internal use only unless stated otherwise.
