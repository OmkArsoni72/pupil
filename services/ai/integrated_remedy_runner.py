"""
Integrated Remedy Runner
Orchestrates Remedy Agent → Content Agent flow for contentGenerationForRemedies route.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig
from uuid import uuid4

from services.ai.remedy_graph import (
    build_remedy_graph,
    REMEDY_CHECKPOINTER,
    RemedyState,
    RemediationPlan
)
from graphs.content_graph import build_content_graph
from services.ai.job_runner import run_job as run_content_job
from services.db_operations.jobs_db import create_job, update_job, get_job
from services.db_operations.remedy_db import create_remedy_plan, update_remedy_plan_status

class IntegratedRemedyJobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "in_progress", "completed", "failed"
    progress: Optional[int] = None
    error: Optional[str] = None
    remedy_plan_id: Optional[str] = None
    content_job_ids: Optional[List[str]] = None

# In-memory job store for integrated remedy jobs
INTEGRATED_REMEDY_JOBS: Dict[str, IntegratedRemedyJobStatus] = {}

async def run_integrated_remedy_job(
    job_id: str, 
    classified_gaps: List[Dict[str, Any]], 
    student_id: str, 
    teacher_class_id: str, 
    context_refs: Dict[str, Any] = None
) -> None:
    """
    Run the integrated Remedy Agent → Content Agent flow.
    
    Flow:
    1. Remedy Agent classifies gaps and generates remediation plans
    2. For each plan, create Content Agent jobs
    3. Track overall progress and completion
    """
    print(f"\n🚀 [INTEGRATED_REMEDY] Starting integrated remedy job {job_id}")
    print(f"🚀 [INTEGRATED_REMEDY] Processing {len(classified_gaps)} classified gaps")
    print(f"🚀 [INTEGRATED_REMEDY] Student ID: {student_id}")
    
    try:
        # Initialize job in INTEGRATED_REMEDY_JOBS dict if not exists
        if job_id not in INTEGRATED_REMEDY_JOBS:
            INTEGRATED_REMEDY_JOBS[job_id] = IntegratedRemedyJobStatus(job_id=job_id, status="pending")
            print(f"🚀 [INTEGRATED_REMEDY] Initialized job {job_id} in INTEGRATED_REMEDY_JOBS dict")
        
        # Update job status
        INTEGRATED_REMEDY_JOBS[job_id].status = "in_progress"
        INTEGRATED_REMEDY_JOBS[job_id].progress = 10
        await update_job(job_id, status="in_progress", progress=10)
        
        # Step 1: Run Remedy Agent to generate remediation plans
        print(f"🚀 [INTEGRATED_REMEDY] Step 1: Running Remedy Agent...")
        remedy_graph = build_remedy_graph().compile(checkpointer=REMEDY_CHECKPOINTER)
        
        # Convert context_refs to dict if it's a Pydantic model
        context_refs_dict = context_refs
        if hasattr(context_refs, 'model_dump'):
            context_refs_dict = context_refs.model_dump()
        elif context_refs is None:
            context_refs_dict = {}
        else:
            # Ensure it's a plain dict for MongoDB
            context_refs_dict = dict(context_refs) if context_refs else {}
            
        initial_state = RemedyState(
            classified_gaps=classified_gaps,
            student_id=student_id,
            teacher_class_id=teacher_class_id,
            context_refs=context_refs_dict
        )
        
        cfg = RunnableConfig(configurable={"thread_id": job_id})
        remedy_result = await remedy_graph.ainvoke(initial_state, cfg)
        
        print(f"🚀 [INTEGRATED_REMEDY] Remedy Agent completed")
        print(f"🚀 [INTEGRATED_REMEDY] Generated {len(remedy_result.get('final_plans', []))} remediation plans")
        
        # Step 2: Store remedy plan in database
        remedy_plan_id = f"REMEDY_PLAN_{uuid4().hex[:8]}"
        await create_remedy_plan(
            remedy_id=remedy_plan_id,
            student_id=student_id,
            teacher_class_id=teacher_class_id,
            classified_gaps=classified_gaps,
            remediation_plans=[plan.model_dump() if hasattr(plan, 'model_dump') else plan for plan in remedy_result.get('final_plans', [])],
            context_refs=context_refs or {},
            prerequisite_discoveries=remedy_result.get('prerequisite_discoveries', {})
        )
        
        INTEGRATED_REMEDY_JOBS[job_id].remedy_plan_id = remedy_plan_id
        INTEGRATED_REMEDY_JOBS[job_id].progress = 30
        
        # Step 3: Create Content Agent jobs for each remediation plan
        print(f"🚀 [INTEGRATED_REMEDY] Step 2: Creating Content Agent jobs...")
        content_job_ids = []
        
        for i, plan in enumerate(remedy_result.get('final_plans', [])):
            # Handle both Pydantic models and dictionaries
            if hasattr(plan, 'gap_type'):
                gap_type = plan.gap_type
                estimated_duration = plan.estimated_duration_minutes
                selected_modes = plan.selected_modes
                content_specs = plan.content_specifications
            else:
                gap_type = plan.get('gap_type', 'unknown')
                estimated_duration = plan.get('estimated_duration_minutes', 15)
                selected_modes = plan.get('selected_modes', [])
                content_specs = plan.get('content_specifications', {})
            
            print(f"🚀 [INTEGRATED_REMEDY] Creating content job for plan {i+1}: {gap_type}")
            
            # Create Content Agent job
            content_job_id = f"CONTENT_{gap_type}_{uuid4().hex[:8]}"
            
            # Prepare Content Agent request
            content_request = {
                "teacher_class_id": teacher_class_id,
                "student_id": student_id,
                "duration_minutes": estimated_duration,
                "modes": selected_modes,
                "learning_gaps": [{
                    "code": content_specs.get("gap_code", "unknown_gap"), 
                    "evidence": content_specs.get("gap_evidence", [])
                }],
                "context_refs": content_specs.get("context_refs", {}),
                "options": {
                    "remedy_mode": True,
                    "gap_type": gap_type,
                    "content_specifications": content_specs,
                    "remedy_plan_id": remedy_plan_id,
                    "plan_index": i
                }
            }
            
            # Create job in database
            await create_job(content_job_id, route="REMEDY", payload=content_request)
            
            # Start Content Agent job
            asyncio.create_task(run_content_job(content_job_id, "REMEDY", content_request))
            
            content_job_ids.append(content_job_id)
            print(f"🚀 [INTEGRATED_REMEDY] Created content job: {content_job_id}")
        
        # Update job status
        INTEGRATED_REMEDY_JOBS[job_id].content_job_ids = content_job_ids
        INTEGRATED_REMEDY_JOBS[job_id].progress = 50
        
        # Update remedy plan with content job IDs
        await update_remedy_plan_status(
            remedy_id=remedy_plan_id,
            status="content_jobs_created",
            content_job_ids=content_job_ids
        )
        
        # Step 4: Wait for content jobs to complete
        print(f"🚀 [INTEGRATED_REMEDY] Step 3: Monitoring content job completion...")
        
        # Update status to indicate content jobs are running (use valid status)
        INTEGRATED_REMEDY_JOBS[job_id].status = "in_progress"  # Changed from "content_generation"
        INTEGRATED_REMEDY_JOBS[job_id].progress = 60
        await update_job(job_id, status="in_progress", progress=60, result_doc_id=remedy_plan_id)
        
        # Wait for all content jobs to complete
        max_wait_time = 300  # 5 minutes max wait
        check_interval = 5   # Check every 5 seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            all_completed = True
            completed_count = 0
            
            for content_job_id in content_job_ids:
                try:
                    # Check job status from database
                    content_job = await get_job(content_job_id)
                    if content_job:
                        job_status = content_job.get("status", "pending")
                        if job_status == "completed":
                            completed_count += 1
                        elif job_status == "failed":
                            print(f"⚠️ [INTEGRATED_REMEDY] Content job {content_job_id} failed")
                        else:
                            all_completed = False
                    else:
                        all_completed = False
                except Exception as e:
                    print(f"⚠️ [INTEGRATED_REMEDY] Error checking content job {content_job_id}: {str(e)}")
                    all_completed = False
            
            # Update progress based on completed jobs
            progress = 60 + int((completed_count / len(content_job_ids)) * 35)  # 60-95%
            INTEGRATED_REMEDY_JOBS[job_id].progress = progress
            await update_job(job_id, progress=progress)
            
            print(f"🚀 [INTEGRATED_REMEDY] Content jobs progress: {completed_count}/{len(content_job_ids)} completed")
            
            if all_completed:
                break
                
            await asyncio.sleep(check_interval)
            elapsed_time += check_interval
        
        if all_completed:
            # All content jobs completed successfully
            INTEGRATED_REMEDY_JOBS[job_id].status = "completed"
            INTEGRATED_REMEDY_JOBS[job_id].progress = 100
            await update_job(job_id, status="completed", progress=100, result_doc_id=remedy_plan_id)
            await update_remedy_plan_status(remedy_id=remedy_plan_id, status="completed")
            print(f"✅ [INTEGRATED_REMEDY] All content jobs completed successfully")
        else:
            # Timeout or some jobs failed
            INTEGRATED_REMEDY_JOBS[job_id].status = "completed"  # Changed from "partial_completion"
            INTEGRATED_REMEDY_JOBS[job_id].progress = 95
            await update_job(job_id, status="completed", progress=95, result_doc_id=remedy_plan_id)
            print(f"⚠️ [INTEGRATED_REMEDY] Some content jobs may not have completed within timeout")
        
        print(f"✅ [INTEGRATED_REMEDY] Integrated remedy job {job_id} completed successfully")
        print(f"✅ [INTEGRATED_REMEDY] Remedy plan ID: {remedy_plan_id}")
        print(f"✅ [INTEGRATED_REMEDY] Content job IDs: {content_job_ids}")
        
    except Exception as e:
        print(f"❌ [INTEGRATED_REMEDY] Error in integrated remedy job {job_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Update job status to failed
        INTEGRATED_REMEDY_JOBS[job_id].status = "failed"
        INTEGRATED_REMEDY_JOBS[job_id].error = str(e)
        INTEGRATED_REMEDY_JOBS[job_id].progress = 0
        
        try:
            await update_job(job_id, status="failed", error=str(e), progress=0)
            print(f"✅ [INTEGRATED_REMEDY] Updated job {job_id} status to failed in database")
        except Exception as db_error:
            print(f"❌ [INTEGRATED_REMEDY] Failed to update job {job_id} status in database: {str(db_error)}")
        
        # Update remedy plan status if it was created
        if INTEGRATED_REMEDY_JOBS[job_id].remedy_plan_id:
            try:
                await update_remedy_plan_status(
                    remedy_id=INTEGRATED_REMEDY_JOBS[job_id].remedy_plan_id,
                    status="failed"
                )
                print(f"✅ [INTEGRATED_REMEDY] Updated remedy plan {INTEGRATED_REMEDY_JOBS[job_id].remedy_plan_id} status to failed")
            except Exception as remedy_error:
                print(f"❌ [INTEGRATED_REMEDY] Failed to update remedy plan status: {str(remedy_error)}")
        
        # Re-raise the original exception so it's properly handled by the calling code
        raise
