# routes/content.py
from fastapi import HTTPException, APIRouter
# from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from uuid import uuid4
import asyncio
# ---- LangGraph / LangChain ----
from services.ai.job_runner import JOBS, JobStatus, run_job
from services.ai.integrated_remedy_runner import INTEGRATED_REMEDY_JOBS, IntegratedRemedyJobStatus, run_integrated_remedy_job
from services.db_operations.jobs_db import update_job
from services.db_operations.jobs_db import create_job, get_job
from services.db_operations.remedy_db import get_remedy_plan, get_latest_remedy_plan_for
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
    type: str  # e.g., "conceptual_gap", "application_gap"
    type_label: str  # e.g., "Conceptual Gap", "Application Gap"
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
    request_meta: Optional[Dict[str, Any]] = None  # e.g., {"test_run": true, "request_origin": "reports_agent"}
    learning_gaps: List[GapEvidence] = Field(min_length=1)
    context_refs: ContextRefs
    modes: Optional[List[Mode]] = None  # Optional - Remedy Agent will determine modes automatically
    options: Optional[Dict[str, Any]] = None  # e.g., {"problems": {"count": 5}, "max_remediation_cycles": 3}

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
    """
    Generate remediation content using Remedy Agent → Content Agent flow.
    
    This endpoint:
    1. Uses Remedy Agent to classify gaps and generate remediation plans
    2. Passes those plans to Content Agent to generate learning content
    3. Returns job status for tracking
    """
    job_id = f"JOB_REM_{uuid4().hex[:8]}"
    print(f"Creating integrated remedy job: {job_id}")
    
    # Create integrated remedy job status
    INTEGRATED_REMEDY_JOBS[job_id] = IntegratedRemedyJobStatus(
        job_id=job_id,
        status="pending",
        progress=0
    )
    print(f"✅ [REMEDY_ROUTE] Created integrated remedy job: {job_id}")
    
    # Also create in regular jobs store for compatibility
    JOBS[job_id] = JobStatus(job_id=job_id, status="pending", progress=0)
    print(f"✅ [REMEDY_ROUTE] Job {job_id} added to in-memory store")
    print(f"✅ [REMEDY_ROUTE] Current JOBS keys: {list(JOBS.keys())}")
    print(f"✅ [REMEDY_ROUTE] Current INTEGRATED_REMEDY_JOBS keys: {list(INTEGRATED_REMEDY_JOBS.keys())}")
    
    try:
        await create_job(job_id, route="REMEDY", payload=payload.model_dump())
        print(f"Job {job_id} created in DB successfully")
    except Exception as e:
        print(f"Failed to create job {job_id} in DB: {str(e)}")
        # Continue anyway, the job is in memory
    
    # Start integrated remedy job (Remedy Agent → Content Agent)
    try:
        asyncio.create_task(run_integrated_remedy_job(
            job_id=job_id,
            classified_gaps=[gap.model_dump() for gap in payload.learning_gaps],
            student_id=payload.student_id,
            teacher_class_id=payload.teacher_class_id,
            context_refs=payload.context_refs.model_dump() if hasattr(payload.context_refs, 'model_dump') else payload.context_refs
        ))
        print(f"Integrated remedy job {job_id} task created")
    except Exception as e:
        print(f"❌ [CONTENT_ROUTE] Failed to create integrated remedy job {job_id}: {str(e)}")
        # Update job status to failed
        JOBS[job_id].status = "failed"
        JOBS[job_id].error = str(e)
        JOBS[job_id].progress = 0
        
        try:
            await update_job(job_id, status="failed", error=str(e), progress=0)
            print(f"✅ [CONTENT_ROUTE] Updated job {job_id} status to failed in database")
        except Exception as db_error:
            print(f"❌ [CONTENT_ROUTE] Failed to update job {job_id} status in database: {str(db_error)}")
        
        raise HTTPException(status_code=500, detail=f"Failed to start remedy job: {str(e)}")
    
    print(f"✅ [REMEDY_ROUTE] Returning job status for {job_id}: {JOBS[job_id]}")
    return JOBS[job_id]

@router.get("/v1/jobs/{job_id}", response_model=JobStatus)
async def job_status(job_id: str):
    print(f"🔍 [JOB_STATUS] Checking status for job: {job_id}")
    print(f"🔍 [JOB_STATUS] Available integrated jobs: {list(INTEGRATED_REMEDY_JOBS.keys())}")
    print(f"🔍 [JOB_STATUS] Available regular jobs: {list(JOBS.keys())}")
    
    # Check if it's an integrated remedy job first
    integrated_job = INTEGRATED_REMEDY_JOBS.get(job_id)
    if integrated_job:
        print(f"✅ [JOB_STATUS] Integrated remedy job {job_id} found: {integrated_job.status}")
        print(f"✅ [JOB_STATUS] Progress: {integrated_job.progress}, Error: {integrated_job.error}")
        # Convert to JobStatus format for compatibility
        # Enrich with aggregated child info if available
        agg = await get_remedy_plan(integrated_job.remedy_plan_id) if integrated_job.remedy_plan_id else None
        result = JobStatus(
            job_id=integrated_job.job_id,
            status=integrated_job.status,
            progress=integrated_job.progress,
            error=integrated_job.error,
            result_doc_id=integrated_job.remedy_plan_id
        )
        # Attach aggregated view as headers-like payload (compatible with response_model)
        # Clients wanting full aggregation should call /v1/jobs/{job_id}/aggregate
        return result
    
    # Check regular jobs
    job = JOBS.get(job_id)
    if job:
        print(f"✅ [JOB_STATUS] Job {job_id} found in memory: {job.status}")
        print(f"✅ [JOB_STATUS] Progress: {job.progress}, Error: {job.error}")
        return job
    
    print(f"🔍 [JOB_STATUS] Job {job_id} not in memory, checking DB...")
    # Fallback to DB if in-memory store doesn't have it (e.g., worker busy or restarted)
    try:
        db_job = await get_job(job_id)
        if not db_job:
            print(f"❌ [JOB_STATUS] Job {job_id} not found in DB either")
            raise HTTPException(404, "job not found")
        
        print(f"✅ [JOB_STATUS] Job {job_id} found in DB: {db_job.get('status')}")
        print(f"✅ [JOB_STATUS] DB Progress: {db_job.get('progress')}, Error: {db_job.get('error')}")
        # return a JobStatus-compatible shape
        return JobStatus(
            job_id=db_job.get("_id"),
            status=db_job.get("status"),
            progress=db_job.get("progress"),
            error=db_job.get("error"),
            result_doc_id=db_job.get("result_doc_id"),
        )
    except Exception as e:
        print(f"❌ [JOB_STATUS] Error getting job {job_id} from DB: {str(e)}")
        raise HTTPException(404, "job not found")

@router.get("/v1/debug/jobs")
async def debug_jobs():
    """Debug endpoint to see all jobs in memory"""
    return {
        "regular_jobs": {k: {"status": v.status, "progress": v.progress, "error": v.error} for k, v in JOBS.items()},
        "integrated_remedy_jobs": {k: {"status": v.status, "progress": v.progress, "error": v.error} for k, v in INTEGRATED_REMEDY_JOBS.items()}
    }

@router.get("/v1/debug/jobs/{job_id}")
async def debug_job_status(job_id: str):
    """Debug endpoint to check job status across all sources"""
    print(f"🔍 [DEBUG] Checking job status for: {job_id}")
    
    try:
        # Check all sources
        db_job = await get_job(job_id)
        mem_job = JOBS.get(job_id)
        integrated_job = INTEGRATED_REMEDY_JOBS.get(job_id)
        
        debug_info = {
            "job_id": job_id,
            "sources": {
                "database": {
                    "found": bool(db_job),
                    "status": db_job.get("status") if db_job else None,
                    "route": db_job.get("route") if db_job else None,
                    "progress": db_job.get("progress") if db_job else None,
                    "result_doc_id": db_job.get("result_doc_id") if db_job else None,
                    "payload_keys": list(db_job.get("payload", {}).keys()) if db_job else []
                },
                "memory": {
                    "found": bool(mem_job),
                    "status": mem_job.status if mem_job else None,
                    "progress": mem_job.progress if mem_job else None,
                    "error": mem_job.error if mem_job else None,
                    "result_doc_id": getattr(mem_job, 'result_doc_id', None) if mem_job else None
                },
                "integrated": {
                    "found": bool(integrated_job),
                    "status": integrated_job.status if integrated_job else None,
                    "progress": integrated_job.progress if integrated_job else None,
                    "error": integrated_job.error if integrated_job else None,
                    "remedy_plan_id": integrated_job.remedy_plan_id if integrated_job else None,
                    "content_job_ids": integrated_job.content_job_ids if integrated_job else []
                }
            }
        }
        
        return debug_info
        
    except Exception as e:
        print(f"❌ [DEBUG] Error debugging job {job_id}: {e}")
        return {"error": str(e)}


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
    print(f"🔍 [CONTENT_ROUTE] Getting content for job: {job_id}")
    
    try:
        # Check all possible job sources
        db_job = await get_job(job_id)
        mem_job = JOBS.get(job_id)
        integrated_job = INTEGRATED_REMEDY_JOBS.get(job_id)
        
        print(f"📊 [CONTENT_ROUTE] Job sources: DB={bool(db_job)}, MEM={bool(mem_job)}, INT={bool(integrated_job)}")
        
        if not db_job and not mem_job and not integrated_job:
            print(f"❌ [CONTENT_ROUTE] Job {job_id} not found in any source")
            raise HTTPException(404, "job not found")
        
        # Determine the authoritative job record (prefer DB, fallback to memory)
        if db_job:
            status_val = db_job.get("status")
            progress_val = db_job.get("progress", 0)
            route = db_job.get("route")
            payload = db_job.get("payload", {})
            result_doc_id = db_job.get("result_doc_id")
            print(f"📊 [CONTENT_ROUTE] Using DB job: {status_val} ({route})")
        elif mem_job:
            status_val = mem_job.status
            progress_val = mem_job.progress
            route = getattr(mem_job, 'route', None)
            payload = getattr(mem_job, 'payload', {})
            result_doc_id = getattr(mem_job, 'result_doc_id', None)
            print(f"📊 [CONTENT_ROUTE] Using memory job: {status_val} ({route})")
        else:  # integrated_job
            status_val = integrated_job.status
            progress_val = integrated_job.progress
            route = "REMEDY"  # Integrated jobs are always REMEDY
            payload = {}  # Integrated jobs don't store payload in memory
            result_doc_id = integrated_job.remedy_plan_id
            print(f"📊 [CONTENT_ROUTE] Using integrated job: {status_val} ({route})")
        
        # Check if job is completed
        if status_val != "completed":
            print(f"⚠️ [CONTENT_ROUTE] Job {job_id} not completed yet: {status_val}")
            response.status_code = 202
            return {
                "job_id": job_id,
                "status": status_val,
                "progress": progress_val,
                "message": "Job not completed yet"
            }
        
        print(f"✅ [CONTENT_ROUTE] Job {job_id} is completed, processing {route} route")
        
        # Route-specific content retrieval
        if route == "AHS":
            return await _get_ahs_content(job_id, payload, result_doc_id)
        elif route == "REMEDY":
            return await _get_remedy_content(job_id, payload, result_doc_id, integrated_job)
        else:
            print(f"⚠️ [CONTENT_ROUTE] Unknown route: {route}")
            return {
                "job_id": job_id,
                "route": route,
                "content": None,
                "message": f"Unknown route: {route}"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [CONTENT_ROUTE] Error getting content for job {job_id}: {e}")
        raise HTTPException(500, f"Internal server error: {str(e)}")

async def _get_ahs_content(job_id: str, payload: dict, result_doc_id: str):
    """Get AHS (After Hour Session) content."""
    print(f"📚 [CONTENT_ROUTE] Getting AHS content for job: {job_id}")
    
    # Get session_id from result_doc_id or payload
    session_id = None
    if result_doc_id and isinstance(result_doc_id, str) and result_doc_id.startswith("sessions/"):
        session_id = result_doc_id.split("/", 1)[1]
    if not session_id:
        session_id = payload.get("session_id")
    
    print(f"📊 [CONTENT_ROUTE] Session ID: {session_id}")
    
    if not session_id:
        print("❌ [CONTENT_ROUTE] Missing session_id for AHS route")
        raise HTTPException(500, "completed job missing session_id")
    
    # Get session from database
    try:
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
            print(f"❌ [CONTENT_ROUTE] Session {session_id} not found")
            raise HTTPException(404, "session not found")
        
        after_hour_session = doc.get("afterHourSession", {})
        print(f"✅ [CONTENT_ROUTE] AHS content retrieved: {len(after_hour_session)} keys")
        
        return {
            "job_id": job_id,
            "route": "AHS",
            "session_id": session_id,
            "content": after_hour_session,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [CONTENT_ROUTE] Error retrieving AHS content: {e}")
        raise HTTPException(500, f"Error retrieving session content: {str(e)}")

async def _get_remedy_content(job_id: str, payload: dict, result_doc_id: str, integrated_job):
    """Get REMEDY content."""
    print(f"🎯 [CONTENT_ROUTE] Getting REMEDY content for job: {job_id}")
    
    # Get student_id from payload or result_doc_id
    student_id = payload.get("student_id")
    if (not student_id) and isinstance(result_doc_id, str) and result_doc_id.startswith("student_reports/"):
        student_id = result_doc_id.split("/", 1)[1]
    
    print(f"📊 [CONTENT_ROUTE] Student ID: {student_id}")
    
    if not student_id:
        print("❌ [CONTENT_ROUTE] Missing student_id for REMEDY route")
        raise HTTPException(500, "completed job missing student_id")
    
    # Get student report from database
    try:
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
            print(f"❌ [CONTENT_ROUTE] Student report for {student_id} not found")
            raise HTTPException(404, "student report not found")
        
        remedy_items = (((report_doc or {}).get("report") or {}).get("remedy_report") or [])
        print(f"✅ [CONTENT_ROUTE] REMEDY content retrieved: {len(remedy_items)} items")
        
        return {
            "job_id": job_id,
            "route": "REMEDY",
            "student_id": student_id,
            "content": remedy_items,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [CONTENT_ROUTE] Error retrieving REMEDY content: {e}")
        raise HTTPException(500, f"Error retrieving student report: {str(e)}")

@router.get("/v1/remedyJobs/{job_id}/plans")
async def get_remedy_plans(job_id: str):
    """
    Get the remediation plans generated by a completed remedy job.
    """
    print(f"Getting plans for remedy job: {job_id}")
    
    # Check if it's an integrated remedy job
    integrated_job = INTEGRATED_REMEDY_JOBS.get(job_id)
    # Fallback: rebuild minimal integrated view from DB if memory was reset
    if not integrated_job:
        db_job = await get_job(job_id)
        if not db_job:
            raise HTTPException(404, "Remedy job not found")
        remedy_plan_id = db_job.get("result_doc_id")
        remedy_plan = await get_remedy_plan(remedy_plan_id) if remedy_plan_id else None
        if not remedy_plan:
            # Fallback to latest by (student_id, teacher_class_id)
            payload = db_job.get("payload") or {}
            latest = await get_latest_remedy_plan_for(payload.get("student_id"), payload.get("teacher_class_id"))
            if not latest:
                raise HTTPException(202, f"Job not completed yet. Status: {db_job.get('status')}")
            remedy_plan = latest
            remedy_plan_id = latest.get("_id")
        if not remedy_plan:
            raise HTTPException(404, "Remedy plan not found")
        child_jobs = remedy_plan.get("content_job_ids", [])
        return {
            "job_id": job_id,
            "status": db_job.get("status"),
            "remedy_plan_id": remedy_plan_id,
            "strategy": {
                "classified_gaps": remedy_plan.get("classified_gaps", []),
                "plans": remedy_plan.get("remediation_plans", [])
            },
            "orchestration": {"child_jobs": child_jobs},
            "prerequisite_discoveries": remedy_plan.get("prerequisite_discoveries", {})
        }
    
    if integrated_job.status != "completed":
        raise HTTPException(202, f"Job not completed yet. Status: {integrated_job.status}")
    
    if not integrated_job.remedy_plan_id:
        raise HTTPException(404, "No remedy plan found for this job")
    
    # Get remedy plan from database
    remedy_plan = await get_remedy_plan(integrated_job.remedy_plan_id)
    
    if not remedy_plan:
        raise HTTPException(404, "Remedy plan not found")
    
    # Structured list of child mode jobs (F3) and high-level strategy (F1)
    plans = remedy_plan.get("remediation_plans", [])
    child_jobs = integrated_job.content_job_ids or []
    prerequisite_discoveries = remedy_plan.get("prerequisite_discoveries", {})
    return {
        "job_id": job_id,
        "status": integrated_job.status,
        "remedy_plan_id": integrated_job.remedy_plan_id,
        "strategy": {
            "classified_gaps": remedy_plan.get("classified_gaps", []),
            "plans": plans
        },
        "orchestration": {
            "child_jobs": child_jobs
        },
        "prerequisite_discoveries": prerequisite_discoveries
    }

@router.get("/v1/jobs/{job_id}/aggregate")
async def job_aggregate(job_id: str):
    """Aggregated parent job view: plans, child jobs, content specs, and RAG outputs."""
    integrated_job = INTEGRATED_REMEDY_JOBS.get(job_id)
    if not integrated_job:
        # Fallback using DB
        db_job = await get_job(job_id)
        if not db_job:
            raise HTTPException(404, "Remedy job not found")
        remedy_plan_id = db_job.get("result_doc_id")
        remedy_plan = await get_remedy_plan(remedy_plan_id) if remedy_plan_id else None
        if not remedy_plan:
            payload = db_job.get("payload") or {}
            latest = await get_latest_remedy_plan_for(payload.get("student_id"), payload.get("teacher_class_id"))
            if not latest:
                raise HTTPException(202, f"Job not completed yet. Status: {db_job.get('status')}")
            remedy_plan = latest
            remedy_plan_id = latest.get("_id")
        if not remedy_plan:
            raise HTTPException(404, "Remedy plan not found")
        child_ids = remedy_plan.get("content_job_ids", [])
        content_results = []
        for cid in child_ids:
            try:
                content_result = await job_content(cid, None)
                content_results.append({"content_job_id": cid, "content": content_result.get("content", {})})
            except Exception as e:
                content_results.append({"content_job_id": cid, "error": str(e)})
        return {
            "job": {
                "job_id": job_id,
                "status": db_job.get("status"),
                "progress": db_job.get("progress"),
                "error": db_job.get("error"),
                "remedy_plan_id": remedy_plan_id,
            },
            "strategy": {
                "classified_gaps": remedy_plan.get("classified_gaps", []),
                "plans": remedy_plan.get("remediation_plans", [])
            },
            "orchestration": {"child_jobs": child_ids},
            "prerequisite_discoveries": remedy_plan.get("prerequisite_discoveries", {}),
            "content_specs": content_results
        }
    remedy_plan = await get_remedy_plan(integrated_job.remedy_plan_id) if integrated_job.remedy_plan_id else None
    if not remedy_plan:
        raise HTTPException(404, "Remedy plan not found")

    # Try to collect content results for each child (best-effort)
    content_results = []
    for content_job_id in (integrated_job.content_job_ids or []):
        try:
            content_result = await job_content(content_job_id, None)  # reuse handler
            content_results.append({
                "content_job_id": content_job_id,
                "content": content_result.get("content", {})
            })
        except Exception as e:
            content_results.append({"content_job_id": content_job_id, "error": str(e)})

    # Collect validation summaries for F4
    validation_summaries = []
    try:
        from services.db_operations.base import validation_logs_collection
        import anyio
        def _get_validation_logs():
            cursor = validation_logs_collection.find({}).sort("timestamp", -1).limit(20)
            return list(cursor)
        validation_logs = await anyio.to_thread.run_sync(_get_validation_logs)
        for log in validation_logs:
            validation_summaries.append({
                "mode": log.get("mode"),
                "is_valid": log.get("is_valid"),
                "timestamp": log.get("timestamp"),
                "metadata": log.get("metadata", {})
            })
    except Exception as e:
        print(f"⚠️ [AGGREGATE] Failed to fetch validation logs: {e}")

    return {
        "job": {
            "job_id": integrated_job.job_id,
            "status": integrated_job.status,
            "progress": integrated_job.progress,
            "error": integrated_job.error,
            "remedy_plan_id": integrated_job.remedy_plan_id,
        },
        "strategy": {
            "classified_gaps": remedy_plan.get("classified_gaps", []),
            "plans": remedy_plan.get("remediation_plans", [])
        },
        "orchestration": {
            "child_jobs": integrated_job.content_job_ids or []
        },
        "prerequisite_discoveries": remedy_plan.get("prerequisite_discoveries", {}),
        "content_specs": content_results,
        "validation_summaries": validation_summaries
    }

@router.get("/v1/remedyJobs/{job_id}/content")
async def get_remedy_content(job_id: str):
    """
    Get the final content generated by Content Agent for this remedy job.
    """
    print(f"Getting content for remedy job: {job_id}")
    
    # Get integrated remedy job
    integrated_job = INTEGRATED_REMEDY_JOBS.get(job_id)
    if not integrated_job:
        raise HTTPException(404, "Remedy job not found")
    
    if integrated_job.status not in ["completed", "partial_completion"]:
        raise HTTPException(202, f"Job not completed yet. Status: {integrated_job.status}")
    
    if not integrated_job.content_job_ids:
        raise HTTPException(404, "No content jobs found for this remedy job")
    
    # Get content from each content job
    content_results = []
    successful_jobs = 0
    
    for content_job_id in integrated_job.content_job_ids:
        try:
            # Check if content job is completed first
            content_job = await get_job(content_job_id)
            if not content_job or content_job.get("status") != "completed":
                print(f"Content job {content_job_id} not ready yet, status: {content_job.get('status') if content_job else 'not found'}")
                content_results.append({
                    "content_job_id": content_job_id,
                    "status": content_job.get("status") if content_job else "not_found",
                    "error": "Content job not completed yet"
                })
                continue
            
            # Reuse the existing job_content logic
            content_result = await job_content(content_job_id, None)
            content_results.append({
                "content_job_id": content_job_id,
                "status": "completed",
                "content": content_result.get("content", {})
            })
            successful_jobs += 1
            
        except Exception as e:
            print(f"Error getting content for job {content_job_id}: {str(e)}")
            content_results.append({
                "content_job_id": content_job_id,
                "status": "error",
                "error": str(e)
            })
    
    # Get remedy plan details
    from services.db_operations.remedy_db import get_remedy_plan
    remedy_plan = await get_remedy_plan(integrated_job.remedy_plan_id) if integrated_job.remedy_plan_id else None
    
    return {
        "job_id": job_id,
        "status": integrated_job.status,
        "remedy_plan_id": integrated_job.remedy_plan_id,
        "remedy_plans": remedy_plan.get("remediation_plans", []) if remedy_plan else [],
        "content_results": content_results,
        "successful_jobs": successful_jobs,
        "total_jobs": len(integrated_job.content_job_ids)
    }

