from pydantic import BaseModel
from typing import List, Dict, Union

class Metadata(BaseModel):
    board: str
    grade: int
    subject: str
    exam_type: str
    duration_minutes: int
    total_marks: int

class SchemeSection(BaseModel):
    name: str
    marks_per_question: Dict[str, float]
    negative_marking: Dict[str, float]
    difficulty_distribution_percent: Dict[str, int]
    question_distribution: Dict[str, Dict[str, int]]

class Scheme(BaseModel):
    answer_types: Dict[str, List[str]]  # e.g. {"MCQ": [...], "Integer": [...], "Descriptive": [...]}
    question_formats: List[str]
    sections: List[SchemeSection]

class TemplateModel(BaseModel):
    target_exam: str
    metadata: Metadata
    scheme: Scheme
    instructions: List[str]
