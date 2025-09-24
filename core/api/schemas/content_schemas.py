"""
Content generation schemas for API routes.
Extracted from routes/content.py to maintain exact compatibility.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from core.services.ai.content_graph import Mode

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