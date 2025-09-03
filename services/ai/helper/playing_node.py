from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from services.ai.helper.utils import persist_artifact

async def node_learn_by_playing(state, config: RunnableConfig) -> Dict[str, Any]:
    """
    Node for generating game URLs based on learning gaps.
    """
    print(f"\n🎮 [PLAYING] Starting learn_by_playing node...")
    print(f"🎮 [PLAYING] Route: {state.route}")
    
    gaps = state.req.get("learning_gaps") or []
    print(f"🎮 [PLAYING] Learning gaps: {gaps}")
    
    # Construct game URL
    gap_list = [g if isinstance(g, str) else g.get("code", "") for g in gaps]
    gap_codes = [g for g in gap_list if g]
    
    if not gap_codes:
        gap_codes = ['general']
        print(f"🎮 [PLAYING] No specific gaps found, using 'general'")
    
    url = f"https://games.pupil/launch?gaps={','.join(gap_codes)}"
    
    # Traceability
    job_id = None
    try:
        job_id = (getattr(config, "configurable", {}) or {}).get("thread_id")
    except Exception:
        job_id = None
    payload = {"_meta": {"mode": "PLAYING", "job_id": job_id}, "url": url}
    
    print(f"🎮 [PLAYING] Generated game URL: {url}")
    print(f"🎮 [PLAYING] Persisting artifact to database...")
    
    await persist_artifact(state.route, "PLAYING", payload, state.req)
    print(f"✅ [PLAYING] Playing node completed successfully")
    
    return {}
