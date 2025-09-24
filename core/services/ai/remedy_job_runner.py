import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig
from uuid import uuid4

from core.services.ai.remedy_graph import (
    build_remedy_graph,
    REMEDY_CHECKPOINTER,
    RemedyState,
    RemediationPlan
)
from core.services.ai.content_graph import build_graph as build_content_graph
from core.services.db_operations.jobs_db import create_job, update_job

class RemedyJobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "in_progress", "completed", "failed"
    progress: Optional[int] = None
    error: Optional[str] = None
    remedy_plans: Optional[List[Dict[str, Any]]] = None
    content_job_ids: Optional[List[str]] = None

# In-memory job store for Remedy Agent
REMEDY_JOBS: Dict[str, RemedyJobStatus] = {}

async def run_remedy_job(job_id: str, classified_gaps: List[Dict[str, Any]], student_id: str, teacher_class_id: str, context_refs: Dict[str, Any] = None) -> None:
    """
    Run the Remedy Agent job to generate remediation plans.
    """
    print(f"\n🚀 [REMEDY_JOB_RUNNER] Starting remedy job {job_id}")
    print(f"🚀 [REMEDY_JOB_RUNNER] Processing {len(classified_gaps)} classified gaps")
    print(f"🚀 [REMEDY_JOB_RUNNER] Student ID: {student_id}")
    
    try:
        # Update job status
        REMEDY_JOBS[job_id].status = "in_progress"
        REMEDY_JOBS[job_id].progress = 10
        await update_job(job_id, status="in_progress", progress=10)
        
        # Build Remedy Agent graph
        print(f"🚀 [REMEDY_JOB_RUNNER] Building Remedy Agent graph...")
        remedy_graph = build_remedy_graph().compile(checkpointer=REMEDY_CHECKPOINTER)
        
        # Prepare initial state
        initial_state = RemedyState(
            classified_gaps=classified_gaps,
            student_id=student_id,
            teacher_class_id=teacher_class_id,
            context_refs=context_refs or {}
        )
        
        # Run Remedy Agent
        print(f"🚀 [REMEDY_JOB_RUNNER] Running Remedy Agent...")
        cfg = RunnableConfig(configurable={"thread_id": job_id})
        final_state = await remedy_graph.ainvoke(initial_state, cfg)
        
        # Extract results
        remedy_plans = final_state.final_plans
        content_job_ids = final_state.content_job_ids
        
        print(f"🚀 [REMEDY_JOB_RUNNER] Remedy Agent completed")
        print(f"🚀 [REMEDY_JOB_RUNNER] Generated {len(remedy_plans)} remediation plans")
        print(f"🚀 [REMEDY_JOB_RUNNER] Created {len(content_job_ids)} content jobs")
        
        # Update job status
        REMEDY_JOBS[job_id].status = "completed"
        REMEDY_JOBS[job_id].progress = 100
        REMEDY_JOBS[job_id].remedy_plans = [plan.model_dump() for plan in remedy_plans]
        REMEDY_JOBS[job_id].content_job_ids = content_job_ids
        
        await update_job(job_id, status="completed", progress=100)
        
        print(f"✅ [REMEDY_JOB_RUNNER] Remedy job {job_id} completed successfully")
        
    except Exception as e:
        print(f"❌ [REMEDY_JOB_RUNNER] Error in remedy job {job_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Update job status to failed
        REMEDY_JOBS[job_id].status = "failed"
        REMEDY_JOBS[job_id].error = str(e)
        await update_job(job_id, status="failed", error=str(e))

async def run_content_jobs_from_remedy_plans(remedy_plans: List[RemediationPlan], student_id: str, teacher_class_id: str) -> List[str]:
    """
    Run Content Agent jobs for each remediation plan.
    """
    print(f"\n🔗 [CONTENT_INTEGRATION] Running Content Agent jobs from remedy plans...")
    
    content_job_ids = []
    
    for i, plan in enumerate(remedy_plans):
        print(f"🔗 [CONTENT_INTEGRATION] Processing plan {i+1}: {plan.gap_type}")
        
        # Create Content Agent job
        content_job_id = f"CONTENT_{plan.gap_type}_{uuid4().hex[:8]}"
        
        # Prepare Content Agent request
        content_request = {
            "teacher_class_id": teacher_class_id,
            "student_id": student_id,
            "duration_minutes": plan.estimated_duration_minutes,
            "modes": plan.selected_modes,
            "learning_gaps": [{
                "code": plan.content_specifications["gap_code"], 
                "evidence": plan.content_specifications["gap_evidence"]
            }],
            "context_refs": plan.content_specifications.get("context_refs", {}),
            "options": {
                "remedy_mode": True,
                "gap_type": plan.gap_type,
                "content_specifications": plan.content_specifications
            }
        }
        
        # Create job in database
        await create_job(content_job_id, route="REMEDY_CONTENT", payload=content_request)
        
        # Start Content Agent job
        from core.services.ai.job_runner import run_job
        import asyncio
        asyncio.create_task(run_job(content_job_id, "REMEDY", content_request))
        
        content_job_ids.append(content_job_id)
        print(f"🔗 [CONTENT_INTEGRATION] Created content job: {content_job_id}")
    
    print(f"✅ [CONTENT_INTEGRATION] Created {len(content_job_ids)} content jobs")
    return content_job_ids
