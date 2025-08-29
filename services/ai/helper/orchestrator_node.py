import os
from typing import Dict, Any, List, Literal
from langchain_core.runnables import RunnableConfig
from services.ai.helper.context_loader import build_context_bundle
from langchain_google_genai import ChatGoogleGenerativeAI

# LLM (provider/model can be swapped)
LLM = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.2,
    google_api_key=os.environ["GEMINI_API_KEY"],
)

async def orchestrator_node(state, config: RunnableConfig) -> Dict[str, Any]:
    """
    Orchestrator node that validates inputs and selects modes for content generation.
    """
    print(f"\n🔧 [ORCHESTRATOR] Starting orchestrator node...")
    print(f"🔧 [ORCHESTRATOR] Route: {state.route}")
    print(f"🔧 [ORCHESTRATOR] Request keys: {list(state.req.keys())}")
    
    req = state.req
    route = state.route

    # Validate mandatory fields per PRD
    print(f"🔧 [ORCHESTRATOR] Validating mandatory fields...")
    if route == "AHS":
        if not (req.get("topic") and req.get("context_refs")):
            print(f"❌ [ORCHESTRATOR] AHS validation failed - missing topic or context_refs")
            return {"dependencies_ok": False}
        print(f"✅ [ORCHESTRATOR] AHS validation passed")
    else:  # REMEDY
        if not req.get("learning_gaps"):
            print(f"❌ [ORCHESTRATOR] REMEDY validation failed - missing learning_gaps")
            return {"dependencies_ok": False}
        print(f"✅ [ORCHESTRATOR] REMEDY validation passed")

    # Select modes as requested (you can auto-augment here if needed)
    selected_modes = req["modes"]
    print(f"🔧 [ORCHESTRATOR] Selected modes: {selected_modes}")

    # Build lightweight context bundle from refs for use in prompts
    context_refs = req.get("context_refs") or {}
    context_bundle = await build_context_bundle(context_refs)
    print(f"🔧 [ORCHESTRATOR] Context bundle prepared: lesson_script={bool(context_bundle.get('lesson_script'))}, in_class_qs={len(context_bundle.get('in_class_questions', []))}, recent_sessions={len(context_bundle.get('recent_sessions', []))}")

    # Diagnostics for Remedy: minimal rules-based classifier
    if route == "REMEDY":
        print(f"🔧 [ORCHESTRATOR] Building diagnostics for REMEDY route...")
        gaps = req.get("learning_gaps") or []
        gap_codes = []
        for g in gaps:
            if isinstance(g, str):
                gap_codes.append(g.lower())
            elif isinstance(g, dict) and g.get("code"):
                gap_codes.append(str(g["code"]).lower())

        fundamental_keywords = ["basic", "foundation", "pre", "prereq", "class", "grade", "tables", "phonics"]
        is_fundamental = any(any(k in code for k in fundamental_keywords) for code in gap_codes)

        diagnostics = {
            "gap_classification": "fundamental" if is_fundamental else "procedural",
            "confidence": 0.6 if is_fundamental else 0.55,
            "spiral": [
                {"loop": 1, "focus": gap_codes[:1] or []},
                {"loop": 2, "focus": gap_codes[1:2] or gap_codes[:1] or []},
            ],
        }
        print(f"🔧 [ORCHESTRATOR] Diagnostics built: {diagnostics}")
    else:
        diagnostics = state.diagnostics
        print(f"🔧 [ORCHESTRATOR] Using existing diagnostics: {diagnostics}")
    
    print(f"✅ [ORCHESTRATOR] Orchestrator node completed successfully")
    return {"selected_modes": selected_modes, "diagnostics": diagnostics, "dependencies_ok": True, "context_bundle": context_bundle}
