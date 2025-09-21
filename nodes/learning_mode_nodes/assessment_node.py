import os
import json
from typing import Dict, Any, List, Optional
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from services.ai.helper.utils import persist_artifact, log_validation_result
from services.ai.schemas import LearnByAssessmentPayload

# DB access for pulling prior artifacts
from services.db_operations.base import (
    sessions_collection,
    student_reports_collection,
)
from bson import ObjectId

# LLM (provider/model can be swapped)
LLM = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.2,
    google_api_key=os.environ["GEMINI_API_KEY"],
)


async def _safe_get_session(session_id: str) -> Optional[Dict[str, Any]]:
    try:
        # Motor collections are already async, use them directly
        if ObjectId.is_valid(session_id):
            doc = await sessions_collection.find_one({"_id": ObjectId(session_id)}, {"afterHourSession": 1, "sessionTitle": 1})
            if doc:
                return doc
        return await sessions_collection.find_one({"_id": session_id}, {"afterHourSession": 1, "sessionTitle": 1})
    except Exception as e:
        print(f"[DEBUG] _safe_get_session error: {e}")
        return None


async def _safe_get_student_report(student_id: str) -> Optional[Dict[str, Any]]:
    try:
        # Motor collections are already async, use them directly
        # try common shapes
        doc = await student_reports_collection.find_one({"studentId": student_id}, {"report.remedy_report": 1})
        if doc:
            return doc
        if ObjectId.is_valid(student_id):
            doc = await student_reports_collection.find_one({"studentId": ObjectId(student_id)}, {"report.remedy_report": 1})
            if doc:
                return doc
            doc = await student_reports_collection.find_one({"_id": ObjectId(student_id)}, {"report.remedy_report": 1})
            if doc:
                return doc
        return None
    except Exception as e:
        print(f"[DEBUG] _safe_get_student_report error: {e}")
        return None


def _extract_ahs_snippets(after_hour_session: Dict[str, Any]) -> Dict[str, Any]:
    texts: List[Dict[str, Any]] = after_hour_session.get("texts") or []
    practice: Dict[str, Any] = after_hour_session.get("practiceQuestions") or {}
    assessment_prev: Dict[str, Any] = after_hour_session.get("assessmentQuestions") or {}
    videos: List[Dict[str, Any]] = after_hour_session.get("videos") or []

    # build concise strings for prompt conditioning
    text_preview = []
    for t in texts[:3]:
        # allow either "five_min_summary" or generic fields
        summary = t.get("five_min_summary") or t.get("summary") or str(t)[:200]
        text_preview.append(summary)

    problems_preview = None
    if isinstance(practice, dict):
        problems_preview = (practice.get("problems") or [])[:4]

    return {
        "texts": text_preview,
        "videos": videos[:3],
        "problems": problems_preview,
        "prev_assessment": assessment_prev,
    }


def _extract_remedy_snippets(remedy_report: List[Dict[str, Any]]) -> Dict[str, Any]:
    # take last 2 entries
    recent = (remedy_report or [])[-2:]
    micro_notes = []
    micro_problems = []
    micro_assess = []
    for r in recent:
        art = r.get("artifact") or {}
        kind = r.get("artifact_kind")
        if kind in ("READING", "DOING", "DEBATING", "AUDIO", "WRITING"):
            micro_notes.append(str(art)[:300])
        if kind == "SOLVING":
            micro_problems.extend((art.get("problems") or [])[:3])
        if kind == "ASSESSMENT":
            micro_assess.append(art)
    return {
        "micro_notes": micro_notes[:3],
        "micro_problems": micro_problems[:4],
        "micro_assess": micro_assess[:2],
    }


async def node_learning_by_assessment(state, config: RunnableConfig) -> Dict[str, Any]:
    """
    Generate a short assessment aligned to content produced in this job and learning gaps.
    Produces JSON with: questions (type, difficulty, stem, options?, answer, explanation), coverage_summary.
    """
    print(f"\n📝 [ASSESSMENT] Starting learning_by_assessment node...")
    print(f"📝 [ASSESSMENT] Route: {state.route}")

    req = state.req
    topic = req.get("topic")
    grade = req.get("grade_level")
    learning_gaps = req.get("learning_gaps") or []
    context_bundle = req.get("context_bundle") or {}
    assessment_opts = (req.get("options") or {}).get("assessment", {})
    preferred_types = assessment_opts.get("types") or ["MCQ", "Short", "TrueFalse"]
    desired_count = int(assessment_opts.get("count", 4))

    # F3: Extract F3 orchestration specifications for gap-specific assessment
    f3_orchestration = context_bundle.get("f3_orchestration", {})
    gap_type = f3_orchestration.get("gap_type", "unknown")
    assessment_focus = f3_orchestration.get("assessment_focus", "general")
    content_requirements = f3_orchestration.get("content_requirements", {}).get("assessment", {})
    
    print(f"📝 [ASSESSMENT] F3: Gap type: {gap_type}, Assessment focus: {assessment_focus}")
    print(f"📝 [ASSESSMENT] F3: Content requirements: {content_requirements}")

    # Pull prior artifacts produced earlier in this job from DB (AHS session or Remedy report)
    ahs_snippets: Dict[str, Any] = {}
    remedy_snippets: Dict[str, Any] = {}
    if state.route == "AHS":
        session_id = req.get("session_id")
        sess_doc = await _safe_get_session(session_id) if session_id else None
        ahs_snippets = _extract_ahs_snippets((sess_doc or {}).get("afterHourSession") or {}) if sess_doc else {}
        print(f"📝 [ASSESSMENT] AHS snippets prepared: texts={len(ahs_snippets.get('texts', []))}, videos={len(ahs_snippets.get('videos', []))}")
    else:
        student_id = req.get("student_id")
        rep_doc = await _safe_get_student_report(student_id) if student_id else None
        remedy_report = (((rep_doc or {}).get("report") or {}).get("remedy_report") or [])
        remedy_snippets = _extract_remedy_snippets(remedy_report)
        print(f"📝 [ASSESSMENT] Remedy snippets prepared: micro_problems={len(remedy_snippets.get('micro_problems', []))}")

    # Build structured prompt
    gap_codes: List[str] = []
    for g in learning_gaps:
        if isinstance(g, str):
            gap_codes.append(g)
        elif isinstance(g, dict) and g.get("code"):
            gap_codes.append(g["code"])

    # F3: Build gap-specific assessment prompt
    f3_assessment_instruction = ""
    if assessment_focus == "recall":
        f3_assessment_instruction = "Focus on factual recall and memory. Include questions that test knowledge retention and key term recognition."
    elif assessment_focus == "analysis":
        f3_assessment_instruction = "Focus on analysis and understanding relationships. Include questions that test conceptual understanding and connections."
    elif assessment_focus == "application":
        f3_assessment_instruction = "Focus on practical application and problem-solving. Include questions that test real-world application skills."
    elif assessment_focus == "foundation_check":
        f3_assessment_instruction = "Focus on foundational knowledge validation. Include questions that test prerequisite understanding."
    elif assessment_focus == "retention_check":
        f3_assessment_instruction = "Focus on retention and spaced repetition. Include questions that test long-term memory and recall."
    elif assessment_focus == "engagement_check":
        f3_assessment_instruction = "Focus on engagement and motivation. Include questions that test interest and participation levels."
    
    # F3: Add content requirements to assessment focus
    f3_requirements = []
    if content_requirements.get("recall_focus"):
        f3_requirements.append("Include factual recall questions")
    if content_requirements.get("factual_questions"):
        f3_requirements.append("Include factual knowledge questions")
    if content_requirements.get("analysis_focus"):
        f3_requirements.append("Include analysis and reasoning questions")
    if content_requirements.get("relationship_questions"):
        f3_requirements.append("Include relationship and connection questions")
    if content_requirements.get("application_focus"):
        f3_requirements.append("Include practical application questions")
    if content_requirements.get("problem_solving_questions"):
        f3_requirements.append("Include problem-solving questions")
    if content_requirements.get("foundation_check"):
        f3_requirements.append("Include foundational knowledge validation")
    if content_requirements.get("prerequisite_validation"):
        f3_requirements.append("Include prerequisite understanding questions")
    if content_requirements.get("retention_check"):
        f3_requirements.append("Include retention and memory questions")
    if content_requirements.get("spaced_assessment"):
        f3_requirements.append("Include spaced repetition questions")
    if content_requirements.get("engagement_check"):
        f3_requirements.append("Include engagement and motivation questions")
    if content_requirements.get("motivation_questions"):
        f3_requirements.append("Include motivation and interest questions")
    
    f3_requirements_text = f"F3 Requirements: {', '.join(f3_requirements)}" if f3_requirements else ""

    prompt = (
        f"You are an assessment generator for grade {grade}. Create a short assessment strictly aligned to the provided content and {gap_type} gaps.\n"
        f"Topic: {topic}. Gap Type: {gap_type}. Gaps: {', '.join(gap_codes) if gap_codes else 'none provided'}.\n"
        f"Assessment Focus: {assessment_focus}. {f3_assessment_instruction}\n"
        f"{f3_requirements_text}\n"
        f"Context snippets (may be partial):\n"
        f"- Reading summaries: {json.dumps(ahs_snippets.get('texts') or remedy_snippets.get('micro_notes') or [], ensure_ascii=False)[:800]}\n"
        f"- Practice problems (sample): {json.dumps(ahs_snippets.get('problems') or remedy_snippets.get('micro_problems') or [], ensure_ascii=False)[:800]}\n"
        f"- Previous assessments (if any): {json.dumps(ahs_snippets.get('prev_assessment') or remedy_snippets.get('micro_assess') or [], ensure_ascii=False)[:500]}\n"
        f"- In-class questions (sample): {json.dumps((context_bundle.get('in_class_questions') or [])[:3], ensure_ascii=False)[:600]}\n\n"
        f"Return JSON ONLY with keys: questions, coverage_summary.\n"
        f"questions: array of {desired_count} items. Each item must have: type one of {preferred_types}, difficulty one of ['easy','medium','hard'], stem (string), options (array for MCQ/TrueFalse, omit otherwise), answer (string or letter), explanation (string).\n"
        f"Ensure at least one easy and one medium question; include at least one item targeting the {gap_type} gaps if provided. coverage_summary: array of short strings for key concepts covered."
    )

    print(f"📝 [ASSESSMENT] Sending prompt to LLM...")
    content = await LLM.ainvoke(prompt)
    print(f"📝 [ASSESSMENT] Received response from LLM")

    raw = (content.content or "").strip()
    if not raw:
        print(f"❌ [ASSESSMENT] Empty LLM response; generating fallback")
        payload = {
            "questions": [
                {"type": "MCQ", "difficulty": "easy", "stem": f"Basic check on {topic}", "options": ["A","B","C","D"], "answer": "A", "explanation": "Answer rationale."}
            ],
            "coverage_summary": [topic or "assessment"],
        }
    else:
        try:
            jstart = raw.find('{')
            jend = raw.rfind('}') + 1
            json_str = raw[jstart:jend] if (jstart != -1 and jend > jstart) else raw
            data = json.loads(json_str)
            # normalize/validate minimally
            questions = data.get("questions") if isinstance(data, dict) else None
            if not isinstance(questions, list):
                questions = []
            # coerce each question shape
            norm_qs = []
            for q in questions[:desired_count]:
                if not isinstance(q, dict):
                    continue
                norm_qs.append({
                    "type": q.get("type") or "MCQ",
                    "difficulty": q.get("difficulty") or "easy",
                    "stem": q.get("stem") or "",
                    "options": q.get("options") if isinstance(q.get("options"), list) else None,
                    "answer": q.get("answer") or q.get("answer_key") or "",
                    "explanation": q.get("explanation") or q.get("why") or "",
                })
            coverage = data.get("coverage_summary") if isinstance(data, dict) else []
            if not isinstance(coverage, list):
                coverage = []
            payload = {"questions": norm_qs, "coverage_summary": coverage}
        except Exception as e:
            print(f"❌ [ASSESSMENT] JSON parse error: {str(e)}")
            payload = {"questions": [], "coverage_summary": []}

    # Attach traceability
    job_id = None
    try:
        job_id = (getattr(config, "configurable", {}) or {}).get("thread_id")
    except Exception:
        job_id = None
    payload = {"_meta": {"mode": "ASSESSMENT", "job_id": job_id, "types": preferred_types, "count": desired_count}, **payload}

    print(f"📝 [ASSESSMENT] Persisting artifact to database...")
    await persist_artifact(state.route, "ASSESSMENT", payload, state.req)
    # Validate assessment payload (best-effort) and log
    try:
        _ = LearnByAssessmentPayload(questions=payload.get("questions", []), coverage_summary=payload.get("coverage_summary", []))
        await log_validation_result("ASSESSMENT", True, None, {"questions": len(payload.get("questions", []))})
    except Exception as e:
        await log_validation_result("ASSESSMENT", False, {"error": str(e)}, None)
    print(f"✅ [ASSESSMENT] Assessment node completed successfully")

    return {}
