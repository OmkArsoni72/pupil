from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class IngestRequest(BaseModel):
    paths: Optional[List[str]] = Field(default=None, description="Optional paths to limit ingestion scope")


class QARequest(BaseModel):
    query: str
    grade: Optional[str] = None
    subject: Optional[str] = None
    top_k: int = 8


class PrereqRequest(BaseModel):
    topic: str
    grade: str
    subject: Optional[str] = None
    top_k: int = 12


class QAResponse(BaseModel):
    query: str
    top_k: int
    citations: List[Dict[str, Any]]


class PrerequisiteFloor(BaseModel):
    grade_level: str
    topics: List[Dict[str, Any]]
    estimated_duration_hours: int
    mastery_threshold: float


class PrerequisitesResponse(BaseModel):
    topic: str
    current_grade: str
    subject: Optional[str]
    prerequisite_floors: List[PrerequisiteFloor]
    discovery_method: str