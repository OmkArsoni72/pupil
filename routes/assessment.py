from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from services.ai.assessment_generator import generate_assessment as gen_assessment_task
from services.db_operations.assessment_db import (
    get_assessment_by_job_id, 
    get_assessment_by_id, 
    get_questions_by_ids,
    update_job_status
)
import uuid

router = APIRouter()

class AssessmentGenerateRequest(BaseModel):
    target_exam: str = Field(..., example="CBSE_Grade10_Physics_Monthly")
    exam_type: str = Field(..., example="monthly")
    self_assessment_mode: Optional[str] = Field(None, example="random")
    difficulty: Optional[str] = Field(None, example="easy")
    subject: str = Field(..., example="Physics")
    class_: str = Field(..., alias="class", example="10A")
    teacher_id: Optional[str] = None
    previous_topics: List[str] = []
    learning_gaps: Optional[List[str]] = []
    file_url: Optional[str] = None

class AssessmentStatusResponse(BaseModel):
    job_id: str
    status: str  # "pending", "completed", or "failed"
    assessment_id: Optional[str] = None  # Available when status is 'completed'
    error: Optional[str] = None  # Available when status is 'failed'

@router.post("/assessments/generate", status_code=202)
async def generate_assessment(
    request: AssessmentGenerateRequest,
    background_tasks: BackgroundTasks
):
    job_id = str(uuid.uuid4())
    
    # Add both the status update and the main task to background tasks
    # This ensures the POST returns instantly
    background_tasks.add_task(update_job_status, job_id, "pending")
    background_tasks.add_task(gen_assessment_task, request.dict(), job_id)
    
    return {"job_id": job_id, "status": "pending"}

@router.get("/assessments/status/{job_id}", response_model=AssessmentStatusResponse)
async def get_assessment_status(job_id: str):
    """
    Checks the status of a generation job.
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
    
    return response

@router.get("/assessments/{assessment_id}")
async def get_assessment(assessment_id: str):
    """
    Retrieves the final generated assessment with populated question data.
    """
    assessment = await get_assessment_by_id(assessment_id)
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Populate question_ids with full question data
    if assessment.get("question_ids"):
        questions = await get_questions_by_ids(assessment["question_ids"])
        assessment["questions"] = questions
    
    return assessment
