import os
import json
from typing import Dict, Any
import anyio
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from core.services.ai.schemas import LearnByReadingPayload
from core.services.ai.helper.utils import persist_artifact, log_validation_result
from core.services.ai.helper.teleprompt_with_media import search_image, bucket_name as MEDIA_BUCKET_NAME

# LLM (provider/model can be swapped)
LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    google_api_key=os.environ["GEMINI_API_KEY"],
)

async def node_learn_by_reading(state, config: RunnableConfig) -> Dict[str, Any]:
    """
    Node for generating reading content with structured notes, summaries, and learning materials.
    """
    print(f"\n📖 [READING] Starting learn_by_reading node...")
    print(f"📖 [READING] Route: {state.route}")
    print(f"📖 [READING] Topic: {state.req.get('topic', 'N/A')}")
    
    req = state.req
    topic = req.get("topic") or "selected_gap_focus"
    grade_level = req.get('grade_level', 'NA')
    learning_gaps = req.get('learning_gaps') or []
    context_bundle = req.get("context_bundle") or {}

    # F3: Extract F3 orchestration specifications for gap-specific content
    f3_orchestration = context_bundle.get("f3_orchestration", {})
    gap_type = f3_orchestration.get("gap_type", "unknown")
    content_requirements = f3_orchestration.get("content_requirements", {}).get("reading", {})
    mode_coordination = f3_orchestration.get("mode_coordination", "")

    # Build remedy-focused context if needed
    gap_codes = []
    gap_evidence = []
    for g in learning_gaps:
        if isinstance(g, str):
            gap_codes.append(g)
        elif isinstance(g, dict):
            if g.get("code"):
                gap_codes.append(g.get("code"))
            if g.get("evidence"):
                gap_evidence.extend(g.get("evidence") or [])

    print(f"📖 [READING] Processing topic: {topic}")
    print(f"📖 [READING] Grade level: {grade_level}")
    print(f"📖 [READING] Learning gaps: {learning_gaps}")
    print(f"📖 [READING] F3: Gap type: {gap_type}, Mode coordination: {mode_coordination}")
    print(f"📖 [READING] F3: Content requirements: {content_requirements}")

    if state.route == "REMEDY":
        # F3: Build gap-specific focus text with F3 orchestration
        focus_text = (
            f"Remediate {gap_type} gaps: {', '.join(gap_codes) if gap_codes else 'unspecified'} "
            f"with evidence: {', '.join(gap_evidence) if gap_evidence else 'n/a'}."
        )
        
        # F3: Add gap-specific content requirements to prompt
        f3_requirements = []
        if content_requirements.get("include_glossary"):
            f3_requirements.append("Include comprehensive glossary with key terms")
        if content_requirements.get("include_memory_aids"):
            f3_requirements.append("Include memory aids and mnemonics")
        if content_requirements.get("highlight_key_terms"):
            f3_requirements.append("Highlight and emphasize key terms")
        if content_requirements.get("include_visualizations"):
            f3_requirements.append("Include visualizations and diagrams")
        if content_requirements.get("include_analogies"):
            f3_requirements.append("Include analogies and comparisons")
        if content_requirements.get("include_refreshers"):
            f3_requirements.append("Include refresher content for retention")
        if content_requirements.get("basic_concepts"):
            f3_requirements.append("Focus on basic foundational concepts")
        
        f3_instruction = f"F3 Requirements: {', '.join(f3_requirements)}" if f3_requirements else ""
        
        prompt = f"""
        Create concise, structured notes strictly focused on closing the student's {gap_type} learning gaps.
        {focus_text}
        Grade level: {grade_level}. Mode coordination: {mode_coordination}.
        {f3_instruction}
        Include 1-2 gap-explanations tightly linked to the gaps.
        Use context where relevant:
        - lesson_script excerpt: {str(context_bundle.get('lesson_script'))[:200]}
        - in_class_questions (sample): {str((context_bundle.get('in_class_questions') or [])[:2])}
        - recent_sessions (titles only): {[s.get('title') for s in (context_bundle.get('recent_sessions') or [])]}
        Return only valid JSON with keys: five_min_summary, sections, glossary, memory_hacks, gap_explanations, visual_questions.
        """
    else:
        prompt = f"""
        Create concise, structured notes with 5-min summary, key terms, glossary,
        memory hacks and 1 concept map about: {topic}.
        Grade level: {grade_level}. Include 1 gap-explanation if provided: {learning_gaps}.
        Use context where relevant:
        - lesson_script excerpt: {str(context_bundle.get('lesson_script'))[:200]}
        - in_class_questions (sample): {str((context_bundle.get('in_class_questions') or [])[:2])}
        - recent_sessions (titles only): {[s.get('title') for s in (context_bundle.get('recent_sessions') or [])]}
        Return only valid JSON with keys: five_min_summary, sections, glossary, memory_hacks, gap_explanations, visual_questions.
        """
    
    print(f"📖 [READING] Sending prompt to LLM...")
    content = await LLM.ainvoke(prompt)
    print(f"📖 [READING] Received response from LLM")
    
    # Debug: Check what the LLM actually returned
    raw_content = content.content.strip() if content.content else ""
    print(f"📖 [READING] Raw LLM response length: {len(raw_content)}")
    print(f"📖 [READING] Raw LLM response preview: {raw_content[:200]}...")
    
    if not raw_content:
        print(f"❌ [READING] LLM returned empty response")
        payload = {
            "five_min_summary": f"Summary about {topic}",
            "sections": [],
            "glossary": {},
            "memory_hacks": [],
            "gap_explanations": [],
            "visual_questions": []
        }
        print(f"📖 [READING] Using default fallback content")
    else:
        try:
            # Try to extract JSON from the response (in case it's wrapped in markdown)
            json_start = raw_content.find('{')
            json_end = raw_content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = raw_content[json_start:json_end]
                print(f"📖 [READING] Extracted JSON content: {json_content[:200]}...")
                data = json.loads(json_content)
            else:
                # Try parsing the entire response as JSON
                data = json.loads(raw_content)
            
            print(f"📖 [READING] Parsed JSON data successfully")
            validated = LearnByReadingPayload(**data)
            print(f"📖 [READING] Data validation passed")
            payload = validated.model_dump()
            await log_validation_result("READING", True, None, {"len_sections": len(payload.get("sections", []))})
            print(f"📖 [READING] Final payload prepared")
            
        except json.JSONDecodeError as e:
            print(f"❌ [READING] JSON decode error: {str(e)}")
            print(f"📖 [READING] Raw content that failed to parse: {raw_content}")
            # Create a fallback payload with the raw content
            payload = {"raw": raw_content}
            await log_validation_result("READING", False, {"error": str(e)}, None)
            print(f"📖 [READING] Using raw content as fallback")
            
        except Exception as e:
            print(f"❌ [READING] Error processing LLM response: {str(e)}")
            print(f"📖 [READING] Raw content: {raw_content}")
            payload = {"raw": raw_content}
            await log_validation_result("READING", False, {"error": str(e)}, None)
            print(f"📖 [READING] Using raw content as fallback")
    
    # Prepare minimal lesson context excerpt for visuals
    lesson_context = ""
    if context_bundle.get('lesson_script'):
        lesson_context = str(context_bundle.get('lesson_script'))[:200]
    elif context_bundle.get('in_class_questions'):
        lesson_context = str((context_bundle.get('in_class_questions') or [])[:2])[:200]

    # Generate visual content if available
    visual_assets = []
    if topic and grade_level:
        try:
            print(f"📖 [READING] Generating visual content for topic: {topic}")
            # Generate a concept diagram
            image_url = await anyio.to_thread.run_sync(
                lambda: search_image(
                    grade=grade_level,
                    query=topic,
                    bucket_name=MEDIA_BUCKET_NAME,
                    lesson_context=lesson_context,
                )
            )
            if image_url:
                visual_assets.append({
                    "type": "concept_diagram",
                    "url": image_url,
                    "caption": f"Visual representation of {topic}",
                    "description": f"Educational diagram showing key concepts of {topic}"
                })
                print(f"📖 [READING] Generated concept diagram: {image_url}")
            
            # Generate additional visual for gap explanations if gaps exist
            if gap_codes and len(visual_assets) < 2:
                gap_focus = gap_codes[0] if gap_codes else topic
                gap_image_url = await anyio.to_thread.run_sync(
                    lambda: search_image(
                        grade=grade_level,
                        query=f"explaining {gap_focus} concept",
                        bucket_name=MEDIA_BUCKET_NAME,
                        lesson_context=lesson_context,
                    )
                )
                if gap_image_url:
                    visual_assets.append({
                        "type": "gap_explanation",
                        "url": gap_image_url,
                        "caption": f"Explanation of {gap_focus}",
                        "description": f"Visual aid for understanding {gap_focus}"
                    })
                    print(f"📖 [READING] Generated gap explanation visual: {gap_image_url}")
        except Exception as e:
            print(f"📖 [READING] Error generating visuals: {str(e)}")
            # Continue without visuals if generation fails

    # Add visual assets to payload
    if visual_assets:
        payload["visual_assets"] = visual_assets
        print(f"📖 [READING] Added {len(visual_assets)} visual assets to reading content")

    # Attach traceability metadata
    job_id = None
    try:
        job_id = (getattr(config, "configurable", {}) or {}).get("thread_id")
    except Exception:
        job_id = None
    payload = {"_meta": {"mode": "READING", "job_id": job_id}, **payload}

    print(f"📖 [READING] Persisting artifact to database...")
    await persist_artifact(state.route, "READING", payload, state.req)
    print(f"✅ [READING] Reading node completed successfully")
    
    return {}
