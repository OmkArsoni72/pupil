"""
Schema Node - Fetches assessment templates from database.
Extracted from services/ai/assessment_generator.py
"""

from typing import Dict, Any
from services.ai.schema_agent import SchemaAgent


async def schema_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch schema/template from database."""
    print(f"🔍 [schema_node] Fetching template for: {state['target_exam']}")
    tpl = await SchemaAgent.fetch_template(state["target_exam"])
    print(f"✅ [schema_node] Template fetched: {tpl.get('target_exam', 'N/A') if tpl else 'None'}")
    return {"schema": tpl}
