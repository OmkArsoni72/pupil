import os
from typing import Dict, Any, List
import anyio
from langchain_core.runnables import RunnableConfig
from services.ai.helper.utils import persist_artifact, log_validation_result
from services.ai.helper.teleprompt_with_media import search_youtube_video

async def node_learn_by_watching(state, config: RunnableConfig) -> Dict[str, Any]:
    """
    Node for generating curated YouTube video recommendations based on topic and learning gaps.
    """
    print(f"\n📺 [WATCHING] Starting learn_by_watching node...")
    print(f"📺 [WATCHING] Route: {state.route}")
    print(f"📺 [WATCHING] Topic: {state.req.get('topic', 'N/A')}")
    
    topic = (state.req.get('topic') or '').strip()
    grade = (state.req.get('grade_level') or '').strip()
    context_bundle = state.req.get('context_bundle') or {}
    gaps = state.req.get('learning_gaps') or []
    
    # F3: Extract F3 orchestration specifications for gap-specific content
    f3_orchestration = context_bundle.get("f3_orchestration", {})
    gap_type = f3_orchestration.get("gap_type", "unknown")
    content_requirements = f3_orchestration.get("content_requirements", {}).get("watching", {})
    mode_coordination = f3_orchestration.get("mode_coordination", "")
    
    # Extract gap codes for targeted search
    gap_codes: List[str] = []
    for g in gaps:
        if isinstance(g, str):
            gap_codes.append(g)
        elif isinstance(g, dict) and g.get('code'):
            gap_codes.append(g['code'])
    
    print(f"📺 [WATCHING] F3: Gap type: {gap_type}, Mode coordination: {mode_coordination}")
    print(f"📺 [WATCHING] F3: Content requirements: {content_requirements}")

    # Build lesson context for better video relevance
    lesson_context = ""
    if context_bundle.get('lesson_script'):
        lesson_context = str(context_bundle['lesson_script'])[:200]
    elif context_bundle.get('in_class_questions'):
        lesson_context = str(context_bundle['in_class_questions'][:2])[:200]

    videos = []
    search_attempts = 0
    max_attempts = 3

    # F3: Primary search: gap-type specific
    if topic:
        # F3: Build gap-specific search description
        if gap_type == "knowledge":
            search_desc = f"educational facts about {topic} for students"
        elif gap_type == "conceptual":
            search_desc = f"concept explanation and relationships in {topic}"
        elif gap_type == "application":
            search_desc = f"practical applications and problem solving with {topic}"
        elif gap_type == "foundational":
            search_desc = f"basic concepts and fundamentals of {topic}"
        elif gap_type == "retention":
            search_desc = f"review and refresher content for {topic}"
        elif gap_type == "engagement":
            search_desc = f"fun and engaging content about {topic}"
        else:
            search_desc = topic
        
        print(f"📺 [WATCHING] F3: Searching for {gap_type} gap: {search_desc}")
        video_url = await anyio.to_thread.run_sync(
            lambda: search_youtube_video(
                description=search_desc,
                grade=grade,
                number="1",
                lesson_context=lesson_context,
            )
        )
        if video_url:
            # F3: Gap-specific video titles and summaries
            if gap_type == "knowledge":
                title = f"Key Facts About {topic}"
                summary = f"Educational video covering essential facts and information about {topic} with clear explanations and visual examples."
            elif gap_type == "conceptual":
                title = f"Understanding {topic} Concepts"
                summary = f"Conceptual explanation of {topic} focusing on relationships and underlying principles with visual diagrams."
            elif gap_type == "application":
                title = f"Applying {topic} in Practice"
                summary = f"Practical applications and problem-solving examples using {topic} with step-by-step demonstrations."
            elif gap_type == "foundational":
                title = f"Fundamentals of {topic}"
                summary = f"Basic concepts and foundational knowledge about {topic} designed for building strong understanding."
            elif gap_type == "retention":
                title = f"Review: {topic}"
                summary = f"Review and refresher content for {topic} to reinforce learning and improve retention."
            elif gap_type == "engagement":
                title = f"Fun with {topic}"
                summary = f"Engaging and interactive content about {topic} designed to increase interest and motivation."
            else:
                title = f"Understanding {topic}"
                summary = f"Comprehensive explanation of {topic} with visual examples and step-by-step breakdown."
            
            videos.append({
                "title": title,
                "youtube_id": video_url.split("v=")[-1] if "v=" in video_url else None,
                "url": video_url,
                "summary": summary
            })
            search_attempts += 1

    # Secondary search: gap-focused (if different from topic)
    if gap_codes and search_attempts < max_attempts:
        gap_focus = ", ".join(gap_codes[:2])
        if gap_focus.lower() not in topic.lower():
            print(f"📺 [WATCHING] Searching for gaps: {gap_focus}")
            video_url = await anyio.to_thread.run_sync(
                lambda: search_youtube_video(
                    description=gap_focus,
                    grade=grade,
                    number="2",
                    lesson_context=lesson_context,
                )
            )
            if video_url:
                videos.append({
                    "title": f"Fixing misconceptions: {gap_focus}",
                    "youtube_id": video_url.split("v=")[-1] if "v=" in video_url else None,
                    "url": video_url,
                    "summary": f"Targeted video addressing common misconceptions in {gap_focus} with practical examples."
                })
                search_attempts += 1

    # Fallback: general educational content
    if not videos and topic:
        print(f"📺 [WATCHING] Fallback search for general {topic} content")
        video_url = await anyio.to_thread.run_sync(
            lambda: search_youtube_video(
                description=f"educational {topic} for students",
                grade=grade,
                number="3",
                lesson_context=lesson_context,
            )
        )
        if video_url:
            videos.append({
                "title": f"Educational content on {topic}",
                "youtube_id": video_url.split("v=")[-1] if "v=" in video_url else None,
                "url": video_url,
                "summary": f"Educational video covering {topic} with clear explanations and examples."
            })

    # Ensure we have at least some suggestions
    if not videos:
        print(f"📺 [WATCHING] No videos found, using fallback suggestions")
        videos = [{
            "title": f"Understanding {topic}",
            "youtube_id": None,
            "url": None,
            "summary": f"Search for '{topic}' educational videos on YouTube for grade {grade} students."
        }]

    # Traceability
    job_id = None
    try:
        job_id = (getattr(config, "configurable", {}) or {}).get("thread_id")
    except Exception:
        job_id = None
    
    payload = {
        "_meta": {"mode": "WATCHING", "job_id": job_id},
        "videos": videos[:3],  # Limit to 3 videos
        "search_terms": [topic] + gap_codes[:2] if topic else gap_codes[:2],
        "grade_level": grade,
    }
    # Validate watching payload structure
    try:
        from services.ai.schemas import LearnByWatchingPayload
        # Ensure videos have required fields
        validated_videos = []
        for v in payload["videos"]:
            if v.get("url") and v.get("title"):
                validated_videos.append({"url": v["url"], "title": v["title"]})
        summaries = [v.get("summary", "") for v in payload["videos"] if v.get("summary")]
        _ = LearnByWatchingPayload(videos=validated_videos, summaries=summaries, difficulty=payload.get("grade_level", "medium"))
        await log_validation_result("WATCHING", True, None, {"videos": len(validated_videos), "summaries": len(summaries)})
    except Exception as e:
        await log_validation_result("WATCHING", False, {"error": str(e)}, None)
    
    print(f"📺 [WATCHING] Generated {len(videos)} video recommendations")
    print(f"📺 [WATCHING] Persisting artifact to database...")
    
    await persist_artifact(state.route, "WATCHING", payload, state.req)
    print(f"✅ [WATCHING] Watching node completed successfully")
    
    return {}
