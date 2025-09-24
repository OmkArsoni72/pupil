from fastapi import BackgroundTasks, HTTPException
from typing import Dict, Any
import uuid
from core.api.schemas.assessment_schemas import AssessmentGenerateRequest, AssessmentStatusResponse
from core.workers.assessment_worker import AssessmentWorker
from core.services.db_operations.assessment_db import (
    get_assessment_by_job_id, 
    get_assessment_by_id, 
    get_questions_by_ids,
    update_job_status
)

class AssessmentController:
    """
    Controller for assessment generation operations.
    Preserves all LangGraph workflows and assessment generation business logic.
    """
    
    def __init__(self):
        self.worker = AssessmentWorker()
    
    async def generate_assessment(
        self,
        request: AssessmentGenerateRequest,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """
        Creates a new assessment generation job.
        
        Preserves the exact workflow:
        1. Generate unique job ID
        2. Add status update to background tasks
        3. Add main assessment generation task to background tasks
        4. Return job ID and status immediately
        
        Args:
            request: Assessment generation request with all parameters
            background_tasks: FastAPI background tasks for async processing
            
        Returns:
            Dict with job_id and status
        """
        job_id = str(uuid.uuid4())
        
        # Add both the status update and the main task to background tasks
        # This ensures the POST returns instantly
        background_tasks.add_task(update_job_status, job_id, "pending")
        background_tasks.add_task(self.worker.process_assessment_job, {**request.dict(), "job_id": job_id})
        
        return {"job_id": job_id, "status": "pending"}
    
    @staticmethod
    async def get_assessment_status(job_id: str) -> AssessmentStatusResponse:
        """
        Checks the status of an assessment generation job.
        
        Preserves exact error handling and response format.
        
        Args:
            job_id: The job ID to check status for
            
        Returns:
            AssessmentStatusResponse with job status and optional assessment_id or error
            
        Raises:
            HTTPException: 404 if job not found
        """
        assessment = await get_assessment_by_job_id(job_id)
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Job not found")
        
        response = {
            "job_id": job_id,
            "status": assessment.get("status", "pending")
        }
        
        if assessment.get("status") == "completed":
            response["assessment_id"] = str(assessment.get("_id"))
        elif assessment.get("status") == "failed":
            response["error"] = assessment.get("error", "Unknown error")
        
        return AssessmentStatusResponse(**response)
    
    @staticmethod
    async def get_assessment(assessment_id: str) -> Dict[str, Any]:
        """
        Retrieves the final generated assessment with populated question data.
        
        Preserves exact data population logic and error handling.
        
        Args:
            assessment_id: The assessment ID to retrieve
            
        Returns:
            Dict containing assessment data with populated questions
            
        Raises:
            HTTPException: 404 if assessment not found
        """
        assessment = await get_assessment_by_id(assessment_id)
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Populate question_ids with full question data
        if assessment.get("question_ids"):
            questions = await get_questions_by_ids(assessment["question_ids"])
            assessment["questions"] = questions
        
        return assessment