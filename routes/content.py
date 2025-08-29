# routes/content.py
from fastapi import HTTPException, APIRouter
# from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from uuid import uuid4
import asyncio
# ---- LangGraph / LangChain ----
from services.ai.job_runner import JOBS, JobStatus, run_job
from services.db_operations.jobs_db import create_job, get_job
from services.ai.content_graph import Mode
from fastapi import Response

# ------------------ Pydantic Schemas ------------------

router = APIRouter()

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
    modes: List[Mode] = Field(min_length=1)
    options: Optional[Dict[str, Any]] = None

class RemedyRequest(BaseModel):
    teacher_class_id: str
    student_id: str
    duration_minutes: int = Field(ge=5, le=40)
    learning_gaps: List[GapEvidence] = Field(min_length=1)
    context_refs: ContextRefs
    modes: List[Mode] = Field(min_length=1)
    options: Optional[Dict[str, Any]] = None  # e.g., {"spiral_enable": True, "max_loops": 3}

"""JobStatus model and JOBS store moved to services.ai.job_runner"""

@router.post("/v1/contentGenerationForAHS", response_model=JobStatus, status_code=202)
async def content_generation_for_ahs(payload: AHSRequest):
    job_id = f"JOB_AHS_{uuid4().hex[:8]}"
    JOBS[job_id] = JobStatus(job_id=job_id, status="pending", progress=0)
    await create_job(job_id, route="AHS", payload=payload.model_dump())
    asyncio.create_task(run_job(job_id, "AHS", payload.model_dump()))
    return JOBS[job_id]

@router.post("/v1/contentGenerationForRemedies", response_model=JobStatus, status_code=202)
async def content_generation_for_remedies(payload: RemedyRequest):
    job_id = f"JOB_REM_{uuid4().hex[:8]}"
    print(f"Creating remedy job: {job_id}")
    
    JOBS[job_id] = JobStatus(job_id=job_id, status="pending", progress=0)
    print(f"Job {job_id} added to in-memory store")
    
    try:
        await create_job(job_id, route="REMEDY", payload=payload.model_dump())
        print(f"Job {job_id} created in DB successfully")
    except Exception as e:
        print(f"Failed to create job {job_id} in DB: {str(e)}")
        # Continue anyway, the job is in memory
    
    asyncio.create_task(run_job(job_id, "REMEDY", payload.model_dump()))
    print(f"Job {job_id} task created")
    return JOBS[job_id]

@router.get("/v1/jobs/{job_id}", response_model=JobStatus)
async def job_status(job_id: str):
    print(f"Checking status for job: {job_id}")
    
    job = JOBS.get(job_id)
    if job:
        print(f"Job {job_id} found in memory: {job.status}")
        return job
    
    print(f"Job {job_id} not in memory, checking DB...")
    # Fallback to DB if in-memory store doesn't have it (e.g., worker busy or restarted)
    try:
        db_job = await get_job(job_id)
        if not db_job:
            print(f"Job {job_id} not found in DB either")
            raise HTTPException(404, "job not found")
        
        print(f"Job {job_id} found in DB: {db_job.get('status')}")
        # return a JobStatus-compatible shape
        return JobStatus(
            job_id=db_job.get("_id"),
            status=db_job.get("status"),
            progress=db_job.get("progress"),
            error=db_job.get("error"),
            result_doc_id=db_job.get("result_doc_id"),
        )
    except Exception as e:
        print(f"Error getting job {job_id} from DB: {str(e)}")
        raise HTTPException(404, "job not found")


@router.get("/v1/sessions/{session_id}/afterHourSession")
async def get_after_hour_session(session_id: str):
    from services.db_operations.base import sessions_collection
    from bson import ObjectId
    import anyio

    def _find():
        if ObjectId.is_valid(session_id):
            doc = sessions_collection.find_one({"_id": ObjectId(session_id)}, {"afterHourSession": 1})
            if doc:
                return doc
        return sessions_collection.find_one({"_id": session_id}, {"afterHourSession": 1})
    doc = await anyio.to_thread.run_sync(_find)
    if not doc:
        raise HTTPException(status_code=404, detail="session not found")
    return doc.get("afterHourSession", {})


@router.get("/v1/jobs/{job_id}/content")
async def job_content(job_id: str, response: Response):
    """Return generated content for a job once completed.
    - For AHS: returns sessions.afterHourSession for the job's session_id
    - For REMEDY: returns student_reports.report.remedy_report for the job's student_id
    If job is not yet completed, returns 202 with current status/progress.
    """
    # Prefer DB job for complete record (payload, timestamps)
    db_job = await get_job(job_id)
    mem_job = JOBS.get(job_id)

    if not db_job and not mem_job:
        raise HTTPException(404, "job not found")

    # Determine status
    status_val = (mem_job.status if mem_job else db_job.get("status")) or db_job.get("status")
    progress_val = (mem_job.progress if mem_job else db_job.get("progress"))

    if status_val != "completed":
        response.status_code = 202
        return {
            "job_id": job_id,
            "status": status_val,
            "progress": progress_val,
        }

    route = db_job.get("route") if db_job else None
    payload = db_job.get("payload") if db_job else {}

    if route == "AHS":
        # Get session_id from result_doc_id or payload
        result_doc_id = (mem_job.result_doc_id if mem_job else db_job.get("result_doc_id"))
        session_id = None
        if result_doc_id and isinstance(result_doc_id, str) and result_doc_id.startswith("sessions/"):
            session_id = result_doc_id.split("/", 1)[1]
        if not session_id:
            session_id = (payload or {}).get("session_id")
        if not session_id:
            raise HTTPException(500, "completed job missing session_id")

        # Reuse logic from afterHourSession route
        from services.db_operations.base import sessions_collection
        from bson import ObjectId
        import anyio

        def _find():
            if ObjectId.is_valid(session_id):
                doc = sessions_collection.find_one({"_id": ObjectId(session_id)}, {"afterHourSession": 1})
                if doc:
                    return doc
            return sessions_collection.find_one({"_id": session_id}, {"afterHourSession": 1})

        doc = await anyio.to_thread.run_sync(_find)
        if not doc:
            raise HTTPException(404, "session not found")
        return {
            "job_id": job_id,
            "route": route,
            "content": doc.get("afterHourSession", {}),
        }

    elif route == "REMEDY":
        # For now, return all remedy_report entries for the student in this job
        # Prefer parsing from result_doc_id if present
        result_doc_id = (mem_job.result_doc_id if mem_job else db_job.get("result_doc_id"))
        student_id = (payload or {}).get("student_id")
        if (not student_id) and isinstance(result_doc_id, str) and result_doc_id.startswith("student_reports/"):
            student_id = result_doc_id.split("/", 1)[1]
        if not student_id:
            raise HTTPException(500, "completed job missing student_id")

        from services.db_operations.base import student_reports_collection
        import anyio
        from bson import ObjectId

        def _find_student_report():
            # Try by studentId (string)
            doc = student_reports_collection.find_one({"studentId": student_id}, {"report.remedy_report": 1})
            if doc:
                return doc
            # Try by studentId as ObjectId (if DB uses ObjectId)
            if ObjectId.is_valid(student_id):
                doc = student_reports_collection.find_one({"studentId": ObjectId(student_id)}, {"report.remedy_report": 1})
                if doc:
                    return doc
            # As a last resort, if caller passed an actual document id as student_id, try _id
            if ObjectId.is_valid(student_id):
                doc = student_reports_collection.find_one({"_id": ObjectId(student_id)}, {"report.remedy_report": 1})
                if doc:
                    return doc
            return None

        report_doc = await anyio.to_thread.run_sync(_find_student_report)
        if not report_doc:
            raise HTTPException(404, "student report not found")

        remedy_items = (((report_doc or {}).get("report") or {}).get("remedy_report") or [])
        return {
            "job_id": job_id,
            "route": route,
            "student_id": student_id,
            "content": remedy_items,
        }

    else:
        # Unknown route
        return {
            "job_id": job_id,
            "route": route,
            "content": None,
        }