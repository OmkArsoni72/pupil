"""
Vector Database Schema Definitions for RAG Integration
Defines metadata structures for educational content, learning gaps, and prerequisites.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum

class ContentType(str, Enum):
    """Types of educational content that can be vectorized."""
    LESSON_SCRIPT = "lesson_script"
    QUESTION = "question"
    REMEDIATION_PLAN = "remediation_plan"
    CURRICULUM = "curriculum"
    ASSESSMENT = "assessment"
    LEARNING_OUTCOME = "learning_outcome"

class GapType(str, Enum):
    """Types of learning gaps."""
    KNOWLEDGE = "knowledge"
    CONCEPTUAL = "conceptual"
    APPLICATION = "application"
    FOUNDATIONAL = "foundational"
    RETENTION = "retention"
    ENGAGEMENT = "engagement"

class Subject(str, Enum):
    """Subject areas."""
    MATHEMATICS = "mathematics"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    ENGLISH = "english"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    SCIENCE = "science"

class GradeLevel(str, Enum):
    """Grade levels."""
    KINDERGARTEN = "kindergarten"
    GRADE_1 = "grade_1"
    GRADE_2 = "grade_2"
    GRADE_3 = "grade_3"
    GRADE_4 = "grade_4"
    GRADE_5 = "grade_5"
    GRADE_6 = "grade_6"
    GRADE_7 = "grade_7"
    GRADE_8 = "grade_8"
    GRADE_9 = "grade_9"
    GRADE_10 = "grade_10"
    GRADE_11 = "grade_11"
    GRADE_12 = "grade_12"

class DifficultyLevel(str, Enum):
    """Difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class BaseVectorMetadata(BaseModel):
    """Base metadata for all vector entries."""
    content_type: ContentType
    subject: Subject
    grade_level: GradeLevel
    difficulty: DifficultyLevel
    created_at: str
    updated_at: str
    mongo_id: str  # Reference to original MongoDB document

class EducationalContentMetadata(BaseVectorMetadata):
    """Metadata for educational content vectors."""
    content_type: ContentType = Field(..., description="Type of educational content")
    topic: str = Field(..., description="Main topic or concept")
    chapter: Optional[str] = Field(None, description="Chapter name if applicable")
    period: Optional[str] = Field(None, description="Period or lesson number")
    content_text: str = Field(..., description="Full text content for embedding")
    learning_objectives: List[str] = Field(default_factory=list, description="Learning objectives")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisite topics")
    keywords: List[str] = Field(default_factory=list, description="Key terms and concepts")
    success_rate: Optional[float] = Field(None, description="Success rate if available")
    usage_count: int = Field(default=0, description="How many times this content has been used")
    board: Optional[str] = Field(None, description="Educational board (CBSE, ICSE, etc.)")
    language: str = Field(default="english", description="Content language")

class LearningGapMetadata(BaseVectorMetadata):
    """Metadata for learning gap vectors."""
    content_type: ContentType = ContentType.REMEDIATION_PLAN
    gap_code: str = Field(..., description="Unique identifier for the gap")
    gap_type: GapType = Field(..., description="Type of learning gap")
    evidence: List[str] = Field(default_factory=list, description="Evidence of the gap")
    student_profile: Optional[str] = Field(None, description="Student profile information")
    successful_prerequisites: List[str] = Field(default_factory=list, description="Prerequisites that helped resolve this gap")
    learning_modes_used: List[str] = Field(default_factory=list, description="Learning modes that were effective")
    remediation_success_rate: Optional[float] = Field(None, description="Success rate of remediation")
    time_to_resolve_hours: Optional[float] = Field(None, description="Time taken to resolve the gap")
    similar_gaps: List[str] = Field(default_factory=list, description="Similar gap codes")
    teacher_notes: Optional[str] = Field(None, description="Teacher observations")

class PrerequisiteMetadata(BaseVectorMetadata):
    """Metadata for prerequisite vectors."""
    content_type: ContentType = ContentType.CURRICULUM
    prerequisite_topic: str = Field(..., description="The prerequisite topic")
    target_topics: List[str] = Field(default_factory=list, description="Topics this prerequisite enables")
    priority: int = Field(..., description="Priority level (1=highest)")
    estimated_duration_hours: float = Field(default=2.0, description="Estimated time to master")
    learning_objectives: List[str] = Field(default_factory=list, description="Specific learning objectives")
    assessment_criteria: List[str] = Field(default_factory=list, description="How to assess mastery")
    common_misconceptions: List[str] = Field(default_factory=list, description="Common student misconceptions")
    teaching_strategies: List[str] = Field(default_factory=list, description="Effective teaching strategies")
    prerequisite_chain: List[str] = Field(default_factory=list, description="Other prerequisites this depends on")

class QuestionMetadata(BaseVectorMetadata):
    """Metadata for question vectors."""
    content_type: ContentType = ContentType.QUESTION
    question_text: str = Field(..., description="The question text")
    question_type: str = Field(..., description="Type of question (MCQ, Short, etc.)")
    answer: str = Field(..., description="Correct answer")
    explanation: str = Field(..., description="Answer explanation")
    topics: List[str] = Field(default_factory=list, description="Topics covered")
    learning_outcomes: List[str] = Field(default_factory=list, description="Learning outcomes tested")
    usage_history: List[Dict[str, Any]] = Field(default_factory=list, description="Usage history")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="Performance statistics")
    best_solution: Optional[str] = Field(None, description="Best student solution")
    fastest_solution: Optional[str] = Field(None, description="Fastest solution")

class VectorEntry(BaseModel):
    """Complete vector entry with ID, vector, and metadata."""
    id: str = Field(..., description="Unique vector ID")
    vector: List[float] = Field(..., description="768-dimensional Gemini embedding vector")
    metadata: Union[EducationalContentMetadata, LearningGapMetadata, PrerequisiteMetadata, QuestionMetadata]

# Schema validation functions
def validate_educational_content_metadata(metadata: Dict[str, Any]) -> EducationalContentMetadata:
    """Validate and create educational content metadata."""
    return EducationalContentMetadata(**metadata)

def validate_learning_gap_metadata(metadata: Dict[str, Any]) -> LearningGapMetadata:
    """Validate and create learning gap metadata."""
    return LearningGapMetadata(**metadata)

def validate_prerequisite_metadata(metadata: Dict[str, Any]) -> PrerequisiteMetadata:
    """Validate and create prerequisite metadata."""
    return PrerequisiteMetadata(**metadata)

def validate_question_metadata(metadata: Dict[str, Any]) -> QuestionMetadata:
    """Validate and create question metadata."""
    return QuestionMetadata(**metadata)

# Index-specific metadata filters
def create_grade_level_filter(grade_level: str, include_lower: bool = True) -> Dict[str, Any]:
    """Create filter for grade level queries."""
    if include_lower:
        # Include current grade and lower grades
        grade_mapping = {
            "kindergarten": 0, "grade_1": 1, "grade_2": 2, "grade_3": 3,
            "grade_4": 4, "grade_5": 5, "grade_6": 6, "grade_7": 7,
            "grade_8": 8, "grade_9": 9, "grade_10": 10, "grade_11": 11, "grade_12": 12
        }
        current_level = grade_mapping.get(grade_level, 10)
        return {"grade_level": {"$lte": grade_level}}
    else:
        return {"grade_level": grade_level}

def create_subject_filter(subject: str) -> Dict[str, Any]:
    """Create filter for subject queries."""
    return {"subject": subject}

def create_difficulty_filter(difficulty: str, max_difficulty: bool = True) -> Dict[str, Any]:
    """Create filter for difficulty queries."""
    difficulty_mapping = {"easy": 1, "medium": 2, "hard": 3}
    current_difficulty = difficulty_mapping.get(difficulty, 2)
    
    if max_difficulty:
        # Include current difficulty and lower
        return {"difficulty": {"$lte": difficulty}}
    else:
        return {"difficulty": difficulty}

def create_content_type_filter(content_types: List[str]) -> Dict[str, Any]:
    """Create filter for content type queries."""
    return {"content_type": {"$in": content_types}}

def create_success_rate_filter(min_success_rate: float = 0.0) -> Dict[str, Any]:
    """Create filter for success rate queries."""
    return {"success_rate": {"$gte": min_success_rate}}

# Combined filter creation
def create_combined_filter(
    grade_level: Optional[str] = None,
    subject: Optional[str] = None,
    difficulty: Optional[str] = None,
    content_types: Optional[List[str]] = None,
    min_success_rate: Optional[float] = None,
    include_lower_grades: bool = True
) -> Dict[str, Any]:
    """Create a combined filter for complex queries."""
    filters = {}
    
    if grade_level:
        filters.update(create_grade_level_filter(grade_level, include_lower_grades))
    
    if subject:
        filters.update(create_subject_filter(subject))
    
    if difficulty:
        filters.update(create_difficulty_filter(difficulty))
    
    if content_types:
        filters.update(create_content_type_filter(content_types))
    
    if min_success_rate is not None:
        filters.update(create_success_rate_filter(min_success_rate))
    
    return filters

# Metadata extraction helpers
def extract_educational_content_metadata(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata from lesson script document."""
    return {
        "content_type": "lesson_script",
        "subject": doc.get("subject", "unknown"),
        "grade_level": doc.get("grade_level", "unknown"),
        "difficulty": doc.get("difficulty", "medium"),
        "topic": doc.get("topic", doc.get("chapter", "unknown")),
        "chapter": doc.get("chapter"),
        "period": doc.get("period"),
        "content_text": doc.get("script", doc.get("content", "")),
        "learning_objectives": doc.get("learning_objectives", []),
        "prerequisites": doc.get("prerequisites", []),
        "keywords": doc.get("keywords", []),
        "success_rate": doc.get("success_rate"),
        "usage_count": doc.get("usage_count", 0),
        "board": doc.get("board"),
        "language": doc.get("language", "english"),
        "created_at": doc.get("created_at", ""),
        "updated_at": doc.get("updated_at", ""),
        "mongo_id": str(doc.get("_id", ""))
    }

def extract_question_metadata(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata from question document."""
    return {
        "content_type": "question",
        "subject": doc.get("subject", "unknown"),
        "grade_level": doc.get("grade_level", "unknown"),
        "difficulty": doc.get("difficulty", "medium"),
        "question_text": doc.get("questionText", ""),
        "question_type": doc.get("questionType", "MCQ"),
        "answer": doc.get("answer", {}).get("key", ""),
        "explanation": doc.get("answer", {}).get("explanation", ""),
        "topics": doc.get("topics", []),
        "learning_outcomes": doc.get("learningOutcomes", []),
        "usage_history": doc.get("usageHistory", []),
        "statistics": doc.get("statistics", {}),
        "best_solution": doc.get("bestStudentSolution", {}).get("solutionText"),
        "fastest_solution": doc.get("fastestStudentSolution", {}).get("solutionText"),
        "created_at": doc.get("created_at", ""),
        "updated_at": doc.get("updated_at", ""),
        "mongo_id": str(doc.get("_id", ""))
    }

def extract_remediation_metadata(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata from remediation plan document."""
    return {
        "content_type": "remediation_plan",
        "subject": doc.get("subject", "unknown"),
        "grade_level": doc.get("grade_level", "unknown"),
        "difficulty": doc.get("difficulty", "medium"),
        "gap_code": doc.get("gap_code", ""),
        "gap_type": doc.get("gap_type", "unknown"),
        "evidence": doc.get("evidence", []),
        "student_profile": doc.get("student_profile"),
        "successful_prerequisites": doc.get("successful_prerequisites", []),
        "learning_modes_used": doc.get("learning_modes_used", []),
        "remediation_success_rate": doc.get("remediation_success_rate"),
        "time_to_resolve_hours": doc.get("time_to_resolve_hours"),
        "similar_gaps": doc.get("similar_gaps", []),
        "teacher_notes": doc.get("teacher_notes"),
        "created_at": doc.get("created_at", ""),
        "updated_at": doc.get("updated_at", ""),
        "mongo_id": str(doc.get("_id", ""))
    }
