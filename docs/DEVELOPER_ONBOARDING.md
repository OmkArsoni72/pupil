## PupilPrep: Developer Onboarding Guide

Welcome to the PupilPrep team! This guide gives you a high-level understanding of the system, the code layout in this repository, and how data flows through core features. It is meant to complement the detailed docs under `docs/` and inline code.

---

### 1) High-Level Architecture

PupilPrep is an AI-powered educational platform composed of two primary applications built around a central backend system.

- **PupilTeach**: Web application for educators (Teachers, HODs, Deans) to prepare content, manage classes, deliver assessments, and review performance.
- **PupilLearn**: Student-facing application (mobile-first oriented) that delivers a personalized learning experience from in-class interactions to AI-driven remediation.
- **Backend & AI Engine**: Central brain that handles APIs, business logic, persistence, real-time updates, and AI workflows (content generation, gap analysis, personalization).

The system forms a continuous feedback loop: teachers deliver content → students interact → backend analyzes performance → insights flow back to teachers and adaptive support to students.

---

### 2) Repository Layout (This Repo)

Key directories and their roles:

- `core/` — Main application code

  - `agents/` — Agent orchestration and high-level workflows
  - `api/` — HTTP layer
    - `controllers/` — Request handlers
    - `routes/` — Route registrations
    - `schemas/` — Request/response validation models
  - `graphs/` — Graph-based pipelines or orchestrations
  - `models/` — Domain models and data structures
  - `nodes/` — Modular processing units used in graphs/agents
  - `services/` — Business logic, integrations (RAG, embeddings, Pinecone, etc.)
  - `workers/` — Background jobs and async workers

- `scripts/` — Operational scripts for setup, population, debugging, and demos
- `tests/` — Test suite covering integration and feature flows
- `docs/` — Product specs, migration notes, RAG design, remedy agent docs, and this onboarding guide

Other notable files:

- `main.py` — Entry point to run the backend locally
- `requirements.txt` — Python dependencies

See also: `docs/README.md` for a map of the documentation folders.

---

### 3) Core Product Flows

#### PupilTeach (Educator flows)

1. Lesson & Assessment Preparation (async)

   - Teachers upload source materials (PDFs/docs).
   - Backend AI processes to generate draft lesson scripts and questions → stored in a central `question_bank`.
   - Teachers assemble draft assessments with composition rules (e.g., 80% new, 20% revision) and submit for HOD approval.

2. Live Class Cycle (real-time)

   - Teacher starts a live session and "Pushes Question".
   - Backend broadcasts via real-time channel (e.g., WebSockets) to all students in the class.
   - Student answers stream back; teacher dashboard updates live with comprehension stats.

3. Performance Review & Intervention (async)
   - Post class/assessment, the Gap Identification Engine analyzes performance.
   - Draft After-Hour Session (AHS) module is generated for class-wide gaps.
   - Human-in-the-loop: Teacher reviews/approves AHS before assignment.

#### PupilLearn (Student flows)

1. Onboarding

   - Connect to school to sync timetable, or choose standalone mode.
   - Standalone users take a readiness test to generate a personalized dynamic timetable.

2. Daily Learning Loop
   - In-Class: Receive pushed questions and submit answers (also used for attendance).
   - After-Hour Session (AHS): Hybrid session combining teacher-approved class-wide gaps and AI-generated individual gaps.
   - Remedy Sessions: Short targeted sessions scheduled based on AHS performance.

#### Adaptive Remedy Loop (AI Core Logic)

When a student begins a Remedy Session:

- Gap Classification: Fundamental vs Remembrance vs Application gaps.
- Targeted Intervention: Methods tailor to gap type (e.g., spaced repetition vs practice transfer).
- Spiral Method: If fundamental gap persists, de-escalate to prerequisites (lower floor) until stable, then spiral back up.
- Reporting: Log interactions (time, hints, correctness) feeding continuous personalization and analytics.

For product intent and UX narratives, see:

- `docs/prd/remedy_Agent.md`
- `docs/prd/whole_flow_mermaid.md`
- `docs/prd/pupil_prep_prd.md`

---

### 4) Where Things Live in Code

- API surface: `core/api/routes/` (routing) and `core/api/controllers/` (handlers). Request/response validation in `core/api/schemas/`.
- Domain logic: `core/services/` and `core/nodes/`. Long-running or modular steps often encapsulated as nodes and composed in `core/graphs/`.
- Agents and orchestration: `core/agents/` coordinate multi-step AI workflows.
- Data and models: `core/models/` for domain entities and any schema helpers.
- RAG & Embeddings: See `docs/prd/RAG_SYSTEM_DOCUMENTATION.md`, `docs/prd/RAG_INTEGRATION_README.md`, and scripts like `scripts/deploy_rag_system.py`.
- Pinecone usage: Explore `scripts/populate_pinecone_indexes.py`, `scripts/populate_vectors.py`, and related services under `core/services/`.

---

### 5) Running Locally

1. Python version: see `requirements.txt`. Create and activate a virtualenv.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Environment: copy `.env.example` if present, or check `scripts/debug_env.py` to see required variables.
4. Start backend:
   ```bash
   python main.py
   ```
5. Quick smoke tests:
   ```bash
   python scripts/run_tests.py
   ```

Helpful: `scripts/quick_setup.py`, `scripts/quick_test_pipeline.py`, and `scripts/demo_rag_system.py` for end-to-end checks.

---

### 6) Data & Knowledge Flow (RAG and Vectors)

At a high level:

- Ingestion scripts (`scripts/populate_*`, `scripts/setup_rag.py`) parse PDFs/docs, create embeddings, and upsert to vector stores (e.g., Pinecone).
- Retrieval functions in `core/services/` perform similarity search to power question generation, remediation, and explanations.
- See `docs/prd/RAG_IMPLEMENTATION_SUMMARY.md` and `docs/prd/RAG_TESTING_GUIDE.md` for process details and benchmarks.

---

### 7) Tests to Read First

Start with integration tests to understand expected behavior end-to-end:

- `tests/test_rag_system.py`
- `tests/test_rag_integration.py`
- `tests/test_ncert_ingest_and_query.py`
- `tests/test_remedy_agent.py`
- `tests/test_integrated_remedy.py`

These tests illustrate core flows such as ingestion → retrieval → generation, and the remedy loop orchestration.

---

### 8) Common Developer Tasks

- Add a new API route: create a controller in `core/api/controllers/`, define schema in `core/api/schemas/`, and register in `core/api/routes/`.
- Add a new knowledge source: extend ingestion in `scripts/`, add service functions under `core/services/`, wire into graphs/nodes.
- Modify remedy logic: check `core/agents/`, `core/graphs/`, and `core/nodes/` composing the flow; update tests accordingly.

---

### 9) Real-Time Interactions

Real-time classroom flows typically use a publish/broadcast mechanism (e.g., WebSockets). Teacher actions in PupilTeach emit backend events, which are pushed to enrolled PupilLearn clients. Student answers stream back and update teacher dashboards. Look for real-time utilities and handlers under `core/services/` or `core/api/` depending on implementation.

---

### 10) Documentation Index

Useful deep dives:

- Product specs: `docs/prd/`
- Migrations/Refactors: `docs/migration/`
- Remedy Agent overview: `docs/REMEDY_AGENT_README.md`
- RAG overview: `docs/prd/RAG_SYSTEM_DOCUMENTATION.md`

---

### 11) Conventions

- Prefer explicit, readable code; follow the repository's formatting and linting rules.
- Keep business logic in `services/` or `nodes/`, keep controllers thin.
- Favor integration tests for end-to-end flows; add unit tests for core utilities.

---

If you get stuck:

- Skim the tests and `docs/prd/` first to clarify intent.
- Use scripts in `scripts/` to reproduce flows locally.
- Reach out with file paths and failing tests/screens—fastest path to help.
