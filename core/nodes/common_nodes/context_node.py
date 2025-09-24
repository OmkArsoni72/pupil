"""
Context Node - Gathers context from database.
Extracted from services/ai/assessment_generator.py
"""

from typing import Dict, Any
from core.services.ai.context_agent import ContextAgent


async def context_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Gather context from database."""
    print(f"🔍 [context_node] Gathering context for exam_type: {state.get('exam_type')}")
    ctx = await ContextAgent.gather_context(
        exam_type=state.get("exam_type"),
        previous_topics=state.get("previous_topics", []),
        learning_gaps=state.get("learning_gaps", []),
        file_url=state.get("file_url"),
        self_assessment_mode=state.get("self_assessment_mode"),
        subject=state.get("subject"),
        grade=int(state.get("class_", "10").replace("A", "").replace("B", "")) if state.get("class_") else None
    )
    print(f"✅ [context_node] Context gathered - Topics: {len(ctx.get('selected_topics', []))}, Learning Outcomes: {len(ctx.get('learning_outcomes', []))}")
    return {"context": ctx}
