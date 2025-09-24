"""
Assessment Node - Saves assessment results to database.
Extracted from services/ai/assessment_generator.py
"""

from typing import Dict, Any
from core.services.db_operations.assessment_db import save_assessment, update_job_status


async def assessment_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Save result to database."""
    print(f"💾 [assessment_node] Saving {len(state.get('questions', []))} questions to database")
    # persist and mark job completed
    await save_assessment(state.get("questions"), state.get("job_id"), state)
    await update_job_status(state.get("job_id"), "completed")
    print(f"✅ [assessment_node] Assessment saved successfully with job_id: {state.get('job_id')}")
    return {}
