from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from services.db_operations.content_db import set_ahs_status

async def collector_node(state, config: RunnableConfig) -> Dict[str, Any]:
    """
    Collector node that finalizes the content generation process and updates status.
    """
    print(f"\n📦 [COLLECTOR] Starting collector node...")
    print(f"📦 [COLLECTOR] Route: {state.route}")
    print(f"📦 [COLLECTOR] Session ID: {state.req.get('session_id', 'N/A')}")
    print(f"📦 [COLLECTOR] Student ID: {state.req.get('student_id', 'N/A')}")
    
    # Placeholder: write assembled artifacts into Mongo session/remedy documents and capture IDs
    if state.route == "AHS":
        print(f"📦 [COLLECTOR] Processing AHS route...")
        session_id = state.req.get("session_id")
        
        # Mark session as completed for AHS content generation
        print(f"📦 [COLLECTOR] Setting AHS status to 'completed'...")
        await set_ahs_status(session_id, "completed")
        print(f"📦 [COLLECTOR] AHS status updated successfully")
        
        db_handles = {"session_doc": f"sessions/{session_id}"}
        print(f"📦 [COLLECTOR] AHS DB handles: {db_handles}")
        
    else:
        print(f"📦 [COLLECTOR] Processing REMEDY route...")
        # For Remedy, we don't know the specific remedy id here; store placeholder
        student_id = state.req.get('student_id')
        db_handles = {"remedy_doc": f"student_reports/{student_id}"}
        print(f"📦 [COLLECTOR] REMEDY DB handles: {db_handles}")
    
    print(f"✅ [COLLECTOR] Collector node completed successfully")
    return {"db_handles": db_handles}
