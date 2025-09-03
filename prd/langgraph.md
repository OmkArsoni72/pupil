https://chatgpt.com/share/68a4e02b-8240-8002-954a-79c94dc001a9
Got it — let’s carefully design the best possible graph for your multimodal content agent, considering clarity, scalability, and failure handling. I’ll break it down like a system designer:

Core Principles
FastAPI only speaks JSON in/out.


LangGraph is the workflow orchestrator.


LangChain is embedded inside each agent node (LLM logic, prompt templates, embeddings).


We want extensible, non-blocking, and parallelizable design.



Proposed Graph (9 features)
1. Entry Point
Node: orchestrator


Reads input: {topic, mode}


Decides which branch (agent) to activate.



2. Parallelizable Sub-Agents (9 features → 9 nodes)
explainer_agent → text explanation (LangChain prompt).


quiz_agent → MCQs.


story_agent → story mode (kids-friendly).


diagram_agent → generates diagram/image prompt.


flashcard_agent → Q/A pairs.


summary_agent → TL;DR summary.


exercise_agent → practice problems.


analogies_agent → analogies/metaphors.


assessment_agent → difficulty-scaled test.


Each is an independent LangChain LLM pipeline inside a LangGraph node.

3. Aggregator
Node: collector


Waits for all active agents → merges state into unified JSON.


Handles failures gracefully (e.g., if diagram_agent fails, just omit that field).



4. Exit
Graph terminates at END → FastAPI returns JSON.



Graph Topology
FastAPI request
    |
    v
Orchestrator (decides modes)
    |
    v
 ┌────────────┬────────────┬────────────┐
 v            v            v            v
Explainer   Quiz        Story      Diagram
   v          v            v          v
 ... (all 9 parallel) ...
 └────────────┴────────────┴────────────┘
              |
              v
         Collector
              |
              v
             END → FastAPI response


Pros
Scalable → easy to add/remove agents.


Parallel execution → multiple content types generated at once.


Resilient → collector can merge partial outputs.


Extensible → swap LangChain nodes for custom APIs (e.g., image gen).



Cons
Resource heavy if all 9 run every time.


Needs checkpointing (LangGraph Checkpoint API) for long jobs.


Cost → each sub-agent may trigger separate LLM calls.



Optimization
Orchestrator can prune branches (e.g., only run quiz+diagram if requested).


Could introduce streaming response: partial JSON updates → client (so UI doesn’t wait).



👉 This is the “best graph”: entry → orchestrator → parallel multimodal agents → collector → end.
Do you want me to now show exact JSON state transitions (before orchestrator, after each sub-agent, after collector, final response)? That would make the flow 100% tangible.































































# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, conlist
from typing import List, Dict, Optional, Literal, Any
from uuid import uuid4
import asyncio

# ---- LangGraph / LangChain ----
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

# ------------------ Pydantic Schemas ------------------

Mode = Literal[
    "learn_by_reading",
    "learn_by_writing",
    "learn_by_watching",
    "learn_by_playing",
    "learn_by_doing",
    "learn_by_solving",
    "learn_by_questioning_debating",
    "learn_by_listening_speaking",
    "learning_by_assessment",
]

class ContextRefs(BaseModel):
    lesson_script_id: Optional[str] = None
    in_class_question_ids: Optional[List[str]] = None
    recent_session_ids: Optional[List[str]] = None
    recent_performance: Optional[Dict[str, Any]] = None

class GapEvidence(BaseModel):
    code: str
    evidence: Optional[List[str]] = None

class AHSRequest(BaseModel):
    teacher_class_id: str
    session_id: str
    duration_minutes: int = Field(ge=5, le=90)
    grade_level: str
    curriculum_goal: str
    topic: str
    context_refs: ContextRefs
    learning_gaps: Optional[List[str]] = None
    modes: conlist(Mode, min_items=1)
    options: Optional[Dict[str, Any]] = None

class RemedyRequest(BaseModel):
    teacher_class_id: str
    student_id: str
    duration_minutes: int = Field(ge=5, le=40)
    learning_gaps: conlist(GapEvidence, min_items=1)
    context_refs: ContextRefs
    modes: conlist(Mode, min_items=1)
    options: Optional[Dict[str, Any]] = None  # e.g., {"spiral_enable": True, "max_loops": 3}

class JobStatus(BaseModel):
    job_id: str
    status: Literal["pending", "in_progress", "completed", "failed"]
    progress: Optional[int] = None
    error: Optional[str] = None
    result_doc_id: Optional[str] = None  # e.g., sessions/<id> or content_store/<id>

# --------------- In-memory job store (swap with Redis) ---------------
JOBS: Dict[str, JobStatus] = {}

# ---------------- LangGraph State ----------------
class State(BaseModel):
    # immutable inputs
    route: Literal["AHS", "REMEDY"]
    req: Dict[str, Any]
    # orchestration
    selected_modes: List[Mode] = []
    diagnostics: Dict[str, Any] = {}
    artifacts: Dict[str, Any] = {}     # content_id -> payload/meta
    dependencies_ok: bool = True
    # output handles
    db_handles: Dict[str, str] = {}     # where artifacts are stored (session/remedy ids)

# --------- Shared LLM (swap to your provider/models) ---------
LLM = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# ---------------- Utility: persist & create artifact refs ----------------
async def persist_artifact(route: str, kind: str, payload: Dict[str, Any]) -> str:
    # TODO connect to Mongo and insert; return content_id
    # Map to: sessions.afterHourSession.* (AHS) or student_reports.remedy_report.* (Remedy)
    content_id = f"{route}_{kind}_{uuid4().hex[:8]}"
    # ... DB insert here ...
    return content_id

# ---------------- Orchestrator Node ----------------
async def orchestrator_node(state: State, config: RunnableConfig) -> State:
    req = state.req
    route = state.route

    # Validate mandatory fields per PRD
    if route == "AHS":
        if not (req.get("topic") and req.get("context_refs")):
            state.dependencies_ok = False
            return state
    else:  # REMEDY
        if not req.get("learning_gaps"):
            state.dependencies_ok = False
            return state

    # Select modes as requested (you can auto-augment here if needed)
    state.selected_modes = req["modes"]

    # Diagnostics for Remedy: classify gap & build spiral path
    if route == "REMEDY":
        # TODO: real gap classifier using recent performance & errors
        state.diagnostics = {
            "gap_classification": "fundamental",
            "confidence": 0.7,
            "spiral": [{"loop": 1}, {"loop": 2}]
        }
    return state

# ---------------- Feature Nodes (9 mini-agents) ----------------
# Each returns a content_id + payload; LangChain used inside.

async def node_learn_by_reading(state: State, config: RunnableConfig) -> State:
    req = state.req
    topic = req.get("topic") or "selected_gap_focus"
    prompt = f"""
    Create concise, structured notes with 5-min summary, key terms, glossary,
    memory hacks and 1 concept map about: {topic}.
    Grade level: {req.get('grade_level','NA')}. Include 1 gap-explanation if provided: {req.get('learning_gaps')}.
    JSON only with keys: five_min_summary, sections, glossary, memory_hacks, gap_explanations, visual_questions.
    """
    content = await LLM.ainvoke(prompt)
    payload = {"notes": content.content}
    cid = await persist_artifact(state.route, "READING", payload)
    state.artifacts[cid] = {"type": "reading_notes", "payload": payload}
    return state

async def node_learn_by_writing(state: State, config: RunnableConfig) -> State:
    # AHS-only per PRD; silently skip if Remedies
    if state.route != "AHS":
        return state
    topic = state.req.get("topic")
    prompt = f"Generate 2 open-ended writing prompts to assess recall & understanding on: {topic}."
    content = await LLM.ainvoke(prompt)
    payload = {"prompts": content.content}
    cid = await persist_artifact(state.route, "WRITING", payload)
    state.artifacts[cid] = {"type": "writing_prompts", "payload": payload}
    return state

async def node_learn_by_watching(state: State, config: RunnableConfig) -> State:
    # Stub: replace with YT search tool/DB curated videos
    payload = {"videos": [{"title":"Snell's Law in 5 min","youtube_id":"stub","summary":"..."}]}
    cid = await persist_artifact(state.route, "WATCHING", payload)
    state.artifacts[cid] = {"type": "video_refs", "payload": payload}
    return state

async def node_learn_by_playing(state: State, config: RunnableConfig) -> State:
    gaps = state.req.get("learning_gaps") or []
    # Construct game URL
    url = f"https://games.pupil/launch?gaps={','.join([g if isinstance(g,str) else g['code'] for g in gaps]) or 'general'}"
    payload = {"url": url}
    cid = await persist_artifact(state.route, "PLAYING", payload)
    state.artifacts[cid] = {"type":"game_link", "payload": payload}
    return state

async def node_learn_by_doing(state: State, config: RunnableConfig) -> State:
    topic = state.req.get("topic","Topic")
    prompt = f"Design a safe home experiment for {topic} with materials, steps, and post-task questions. JSON."
    content = await LLM.ainvoke(prompt)
    payload = {"task": content.content}
    cid = await persist_artifact(state.route, "DOING", payload)
    state.artifacts[cid] = {"type":"hands_on_task", "payload": payload}
    return state

async def node_learn_by_solving(state: State, config: RunnableConfig) -> State:
    req = state.req
    topic = req.get("topic","Topic")
    count = req.get("options",{}).get("problems",{}).get("count",4)
    prompt = f"Create {count} problems (progressive difficulty) for {topic} with answers+explanations. JSON."
    content = await LLM.ainvoke(prompt)
    payload = {"problems": content.content}
    cid = await persist_artifact(state.route, "SOLVING", payload)
    state.artifacts[cid] = {"type":"problem_set", "payload": payload}
    return state

async def node_learn_by_questioning_debating(state: State, config: RunnableConfig) -> State:
    prompt = "Build a Socratic debate setup: topic, persona, rules, prompts, closing summary cue. JSON."
    content = await LLM.ainvoke(prompt)
    payload = {"debate": content.content}
    cid = await persist_artifact(state.route, "DEBATING", payload)
    state.artifacts[cid] = {"type":"debate_setup", "payload": payload}
    return state

async def node_learn_by_listening_speaking(state: State, config: RunnableConfig) -> State:
    prompt = "Write a 60s audio script with story + 3 verbal checks. JSON."
    content = await LLM.ainvoke(prompt)
    payload = {"audio_script": content.content}
    cid = await persist_artifact(state.route, "AUDIO", payload)
    state.artifacts[cid] = {"type":"audio_script", "payload": payload}
    return state

async def node_learning_by_assessment(state: State, config: RunnableConfig) -> State:
    # Depend on prior artifacts if present (AHS: reading+solving+writing)
    prompt = "Create a short assessment (3-5 Qs) aligned to prior artifacts, include answer key+why. JSON."
    content = await LLM.ainvoke(prompt)
    payload = {"assessment": content.content}
    cid = await persist_artifact(state.route, "ASSESSMENT", payload)
    state.artifacts[cid] = {"type":"mini_assessment", "payload": payload}
    return state

# ---------------- Collector Node ----------------
async def collector_node(state: State, config: RunnableConfig) -> State:
    # TODO: write assembled artifacts into Mongo session/remedy documents and capture IDs
    if state.route == "AHS":
        state.db_handles["session_doc"] = f"sessions/{state.req['session_id']}"
    else:
        rid = f"REM_{uuid4().hex[:8]}"
        state.db_handles["remedy_doc"] = f"content_store/{rid}"
    return state

# ---------------- Build Graph ----------------
def build_graph(active_modes: List[Mode]) -> StateGraph:
    g = StateGraph(State)
    g.add_node("orchestrator", orchestrator_node)
    g.add_node("collector", collector_node)

    # feature nodes
    nodes = {
        "learn_by_reading": node_learn_by_reading,
        "learn_by_writing": node_learn_by_writing,
        "learn_by_watching": node_learn_by_watching,
        "learn_by_playing": node_learn_by_playing,
        "learn_by_doing": node_learn_by_doing,
        "learn_by_solving": node_learn_by_solving,
        "learn_by_questioning_debating": node_learn_by_questioning_debating,
        "learn_by_listening_speaking": node_learn_by_listening_speaking,
        "learning_by_assessment": node_learning_by_assessment,
    }
    for name, fn in nodes.items():
        g.add_node(name, fn)

    # edges
    g.set_entry_point("orchestrator")
    for m in active_modes:
        g.add_edge("orchestrator", m)
    g.add_edge("learn_by_reading", "collector")
    g.add_edge("learn_by_writing", "collector")
    g.add_edge("learn_by_watching", "collector")
    g.add_edge("learn_by_playing", "collector")
    g.add_edge("learn_by_doing", "collector")
    g.add_edge("learn_by_solving", "collector")
    g.add_edge("learn_by_questioning_debating", "collector")
    g.add_edge("learn_by_listening_speaking", "collector")
    g.add_edge("learning_by_assessment", "collector")
    g.add_edge("collector", END)

    return g

CHECKPOINTER = MemorySaver()  # swap with Redis or DB checkpoint for resilience

# ---------------- FastAPI ----------------
app = FastAPI()

async def run_job(job_id: str, route: Literal["AHS","REMEDY"], req: Dict[str, Any]) -> None:
    try:
        JOBS[job_id].status = "in_progress"
        cfg = RunnableConfig(configurable={"thread_id": job_id})

        graph = build_graph(req["modes"]).compile(checkpointer=CHECKPOINTER)
        init_state = State(route=route, req=req)
        final_state: State = await graph.ainvoke(init_state, cfg)

        # choose final doc handle
        result_doc_id = final_state.db_handles.get("session_doc") or final_state.db_handles.get("remedy_doc")

        JOBS[job_id].status = "completed"
        JOBS[job_id].progress = 100
        JOBS[job_id].result_doc_id = result_doc_id
    except Exception as e:
        JOBS[job_id].status = "failed"
        JOBS[job_id].error = str(e)

@app.post("/v1/contentGenerationForAHS", response_model=JobStatus, status_code=202)
async def content_generation_for_ahs(payload: AHSRequest):
    job_id = f"JOB_AHS_{uuid4().hex[:6]}"
    JOBS[job_id] = JobStatus(job_id=job_id, status="pending", progress=0)
    asyncio.create_task(run_job(job_id, "AHS", payload.model_dump()))
    return JOBS[job_id]

@app.post("/v1/contentGenerationForRemedies", response_model=JobStatus, status_code=202)
async def content_generation_for_remedies(payload: RemedyRequest):
    job_id = f"JOB_REM_{uuid4().hex[:6]}"
    JOBS[job_id] = JobStatus(job_id=job_id, status="pending", progress=0)
    asyncio.create_task(run_job(job_id, "REMEDY", payload.model_dump()))
    return JOBS[job_id]

@app.get("/v1/jobs/{job_id}", response_model=JobStatus)
async def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job: raise HTTPException(404, "job not found")
    return job


