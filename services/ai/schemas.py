from __future__ import annotations

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class ReadingSection(BaseModel):
    title: str
    bullets: List[str] = Field(default_factory=list)


class LearnByReadingPayload(BaseModel):
    five_min_summary: str
    sections: List[ReadingSection] = Field(default_factory=list)
    glossary: Dict[str, str] = Field(default_factory=dict)
    memory_hacks: List[str] = Field(default_factory=list)
    gap_explanations: Optional[List[str]] = None
    visual_questions: List[str] = Field(default_factory=list)
    visual_assets: Optional[List[Dict[str, str]]] = None
    difficulty: Optional[str] = Field(default=None, description="easy|medium|hard")


class LearnByWritingPayload(BaseModel):
    prompts: List[str] = Field(default_factory=list, min_items=1)
    difficulty: Optional[str] = Field(default=None)


class LearnByDoingPayload(BaseModel):
    materials: List[str] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    post_task_questions: List[str] = Field(default_factory=list)
    safety_notes: List[str] = Field(default_factory=list)
    evaluation_criteria: List[str] = Field(default_factory=list)
    difficulty: Optional[str] = Field(default=None)


class LearnByListeningSpeakingPayload(BaseModel):
    title: Optional[str] = None
    script: str
    verbal_checks: List[str] = Field(default_factory=list, min_items=1)
    difficulty: Optional[str] = Field(default=None)


# Additional schemas for modes to enforce minimal structure
class LearnByWatchingPayload(BaseModel):
    videos: List[Dict[str, str]] = Field(default_factory=list)
    summaries: Optional[List[str]] = None
    difficulty: Optional[str] = Field(default=None)

class LearnByPlayingPayload(BaseModel):
    game_links: List[str] = Field(default_factory=list)
    objectives: List[str] = Field(default_factory=list)
    difficulty: Optional[str] = Field(default=None)

class ProblemItem(BaseModel):
    difficulty: str
    question: str
    solution: str

class LearnBySolvingPayload(BaseModel):
    problems: List[ProblemItem] = Field(default_factory=list)
    scheduling_hints: List[str] = Field(default_factory=list)
    difficulty: Optional[str] = Field(default=None)

class LearnByDebatingPayload(BaseModel):
    settings: Dict[str, Any] = Field(default_factory=dict)
    personas: Dict[str, Any] = Field(default_factory=dict)
    prompts: List[str] = Field(default_factory=list)
    closing_summary_cue: str | None = None
    difficulty: Optional[str] = Field(default=None)


