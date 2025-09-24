from fastapi import APIRouter, BackgroundTasks
from api.schemas.assessment_schemas import AssessmentGenerateRequest, AssessmentStatusResponse
from api.controllers.assessment_controller import AssessmentController

router = APIRouter()
controller = AssessmentController()

@router.post("/assessments/generate", status_code=202)
async def generate_assessment(
    request: AssessmentGenerateRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate a new assessment using LangGraph workflows.
    
    This endpoint triggers the assessment generation process which includes:
    - Schema agent for assessment structure
    - Context agent for relevant content
    - Question generator workflows
    
    Returns immediately with job_id for status tracking.
    """
    return await controller.generate_assessment(request, background_tasks)

@router.get("/assessments/status/{job_id}", response_model=AssessmentStatusResponse)
async def get_assessment_status(job_id: str):
    """
    Check the status of an assessment generation job.
    
    Returns:
    - pending: Job is still processing
    - completed: Assessment is ready (includes assessment_id)
    - failed: Generation failed (includes error message)
    """
    return await AssessmentController.get_assessment_status(job_id)

@router.get("/assessments/{assessment_id}")
async def get_assessment(assessment_id: str):
    """
    Retrieve the final generated assessment with populated question data.
    
    Returns the complete assessment including:
    - Assessment metadata
    - Full question objects (populated from question_ids)
    - All generated content from LangGraph workflows
    """
    return await AssessmentController.get_assessment(assessment_id)