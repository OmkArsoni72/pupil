from __future__ import annotations

from typing import List, Dict, Optional
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


class LearnByWritingPayload(BaseModel):
    prompts: List[str] = Field(default_factory=list, min_items=1)


class LearnByDoingPayload(BaseModel):
    materials: List[str] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    post_task_questions: List[str] = Field(default_factory=list)
    safety_notes: List[str] = Field(default_factory=list)
    evaluation_criteria: List[str] = Field(default_factory=list)


class LearnByListeningSpeakingPayload(BaseModel):
    title: Optional[str] = None
    script: str
    verbal_checks: List[str] = Field(default_factory=list, min_items=1)


