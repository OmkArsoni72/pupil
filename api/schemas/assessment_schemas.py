from pydantic import BaseModel, Field
from typing import List, Optional

class AssessmentGenerateRequest(BaseModel):
    target_exam: str = Field(..., example="CBSE_Grade10_Physics_Monthly")
    exam_type: str = Field(..., example="monthly")
    self_assessment_mode: Optional[str] = Field(None, example="random")
    difficulty: Optional[str] = Field(None, example="easy")
    subject: str = Field(..., example="Physics")
    class_: str = Field(..., alias="class", example="10A")
    
    class Config:
        populate_by_name = True
    teacher_id: Optional[str] = None
    previous_topics: List[str] = []
    learning_gaps: Optional[List[str]] = []
    file_url: Optional[str] = None

class AssessmentStatusResponse(BaseModel):
    job_id: str
    status: str  # "pending", "completed", or "failed"
    assessment_id: Optional[str] = None  # Available when status is 'completed'
    error: Optional[str] = None  # Available when status is 'failed'