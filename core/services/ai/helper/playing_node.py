from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from services.ai.helper.utils import persist_artifact, log_validation_result

async def node_learn_by_playing(state, config: RunnableConfig) -> Dict[str, Any]:
    """
    Node for generating game URLs based on learning gaps.
    """
    print(f"\n🎮 [PLAYING] Starting learn_by_playing node...")
    print(f"🎮 [PLAYING] Route: {state.route}")
    
    gaps = state.req.get("learning_gaps") or []
    context_bundle = state.req.get("context_bundle") or {}
    
    # F3: Extract F3 orchestration specifications for gap-specific content
    f3_orchestration = context_bundle.get("f3_orchestration", {})
    gap_type = f3_orchestration.get("gap_type", "unknown")
    content_requirements = f3_orchestration.get("content_requirements", {}).get("playing", {})
    mode_coordination = f3_orchestration.get("mode_coordination", "")
    
    print(f"🎮 [PLAYING] Learning gaps: {gaps}")
    print(f"🎮 [PLAYING] F3: Gap type: {gap_type}, Mode coordination: {mode_coordination}")
    print(f"🎮 [PLAYING] F3: Content requirements: {content_requirements}")
    
    # Construct game URL with F3 gap-type specific parameters
    gap_list = [g if isinstance(g, str) else g.get("code", "") for g in gaps]
    gap_codes = [g for g in gap_list if g]
    
    if not gap_codes:
        gap_codes = ['general']
        print(f"🎮 [PLAYING] No specific gaps found, using 'general'")
    
    # F3: Add gap-type specific game parameters
    game_params = {
        "gaps": ','.join(gap_codes),
        "gap_type": gap_type,
        "mode_coordination": mode_coordination
    }
    
    # F3: Add retention-specific parameters for retention gaps
    if gap_type == "retention":
        game_params.update({
            "retention_mode": "true",
            "memory_aids": "true",
            "spaced_repetition": "true"
        })
    elif gap_type == "engagement":
        game_params.update({
            "engagement_mode": "true",
            "gamification": "true",
            "interactive_elements": "true"
        })
    elif gap_type == "application":
        game_params.update({
            "application_mode": "true",
            "problem_based": "true",
            "skill_practice": "true"
        })
    
    # Build URL with parameters
    param_string = '&'.join([f"{k}={v}" for k, v in game_params.items()])
    url = f"https://games.pupil/launch?{param_string}"
    
    # Traceability
    job_id = None
    try:
        job_id = (getattr(config, "configurable", {}) or {}).get("thread_id")
    except Exception:
        job_id = None
    # F3: Build gap-specific objectives
    objectives = []
    if gap_type == "retention":
        objectives = [
            f"Memory reinforcement for {', '.join(gap_codes) if gap_codes else 'general'}",
            "Spaced repetition practice",
            "Retention improvement through gamification"
        ]
    elif gap_type == "engagement":
        objectives = [
            f"Engagement building for {', '.join(gap_codes) if gap_codes else 'general'}",
            "Motivation enhancement",
            "Interactive learning experience"
        ]
    elif gap_type == "application":
        objectives = [
            f"Skill practice for {', '.join(gap_codes) if gap_codes else 'general'}",
            "Problem-solving application",
            "Practical skill development"
        ]
    elif gap_type == "conceptual":
        objectives = [
            f"Conceptual understanding for {', '.join(gap_codes) if gap_codes else 'general'}",
            "Relationship building",
            "Conceptual practice"
        ]
    elif gap_type == "knowledge":
        objectives = [
            f"Knowledge reinforcement for {', '.join(gap_codes) if gap_codes else 'general'}",
            "Factual recall practice",
            "Information retention"
        ]
    elif gap_type == "foundational":
        objectives = [
            f"Foundation building for {', '.join(gap_codes) if gap_codes else 'general'}",
            "Prerequisite practice",
            "Basic concept reinforcement"
        ]
    else:
        objectives = [f"Practice {', '.join(gap_codes) if gap_codes else 'general'}"]
    
    payload = {
        "_meta": {"mode": "PLAYING", "job_id": job_id}, 
        "url": url,
        "objectives": objectives,
        "gap_type": gap_type,
        "f3_orchestration": True
    }
    
    print(f"🎮 [PLAYING] F3: Generated {gap_type} game URL: {url}")
    print(f"🎮 [PLAYING] F3: Objectives: {objectives}")
    print(f"🎮 [PLAYING] Persisting artifact to database...")
    
    await persist_artifact(state.route, "PLAYING", payload, state.req)
    # Validate playing payload structure
    try:
        from services.ai.schemas import LearnByPlayingPayload
        _ = LearnByPlayingPayload(game_links=[url] if url else [], objectives=objectives, difficulty="medium")
        await log_validation_result("PLAYING", True, None, {"has_url": bool(url), "objectives": len(objectives), "gap_type": gap_type})
    except Exception as e:
        await log_validation_result("PLAYING", False, {"error": str(e)}, None)
    print(f"✅ [PLAYING] F3: Playing node completed successfully for {gap_type} gaps")
    
    return {}
