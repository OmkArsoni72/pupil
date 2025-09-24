import os
import json
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from core.services.ai.schemas import LearnByListeningSpeakingPayload
from core.services.ai.helper.utils import persist_artifact, log_validation_result

# LLM (provider/model can be swapped)
LLM = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.2,
    google_api_key=os.environ["GEMINI_API_KEY"],
)

async def node_learn_by_listening_speaking(state, config: RunnableConfig) -> Dict[str, Any]:
    """
    Node for generating audio scripts and verbal interaction content.
    """
    print(f"\n🎧 [LISTENING_SPEAKING] Starting learn_by_listening_speaking node...")
    print(f"🎧 [LISTENING_SPEAKING] Route: {state.route}")
    print(f"🎧 [LISTENING_SPEAKING] Topic: {state.req.get('topic', 'N/A')}")
    
    topic = state.req.get('topic', 'the topic')
    learning_gaps = state.req.get('learning_gaps') or []
    context_bundle = state.req.get('context_bundle') or {}
    
    # F3: Extract F3 orchestration specifications for gap-specific content
    f3_orchestration = context_bundle.get("f3_orchestration", {})
    gap_type = f3_orchestration.get("gap_type", "unknown")
    content_requirements = f3_orchestration.get("content_requirements", {}).get("listening_speaking", {})
    mode_coordination = f3_orchestration.get("mode_coordination", "")
    
    gap_codes = []
    for g in learning_gaps:
        if isinstance(g, str):
            gap_codes.append(g)
        elif isinstance(g, dict) and g.get('code'):
            gap_codes.append(g['code'])
    
    print(f"🎧 [LISTENING_SPEAKING] F3: Gap type: {gap_type}, Mode coordination: {mode_coordination}")
    print(f"🎧 [LISTENING_SPEAKING] F3: Content requirements: {content_requirements}")
    
    if state.route == 'REMEDY':
        focus = ", ".join(gap_codes) if gap_codes else topic
        
        # F3: Build gap-specific audio script instructions
        f3_audio_instruction = ""
        if gap_type == "engagement":
            f3_audio_instruction = "Focus on engagement and motivation. Create an engaging, interactive audio script that sparks interest and encourages participation. Use storytelling, questions, and interactive elements to build engagement and motivation."
        elif gap_type == "conceptual":
            f3_audio_instruction = "Focus on conceptual understanding. Create an audio script that helps students understand relationships and underlying principles through clear explanations and examples."
        elif gap_type == "knowledge":
            f3_audio_instruction = "Focus on factual knowledge delivery. Create an audio script that presents key facts and information in an engaging, memorable way."
        elif gap_type == "application":
            f3_audio_instruction = "Focus on practical application. Create an audio script that demonstrates real-world applications and problem-solving approaches."
        elif gap_type == "foundational":
            f3_audio_instruction = "Focus on foundational knowledge. Create an audio script that builds basic concepts and prerequisites in a clear, accessible way."
        elif gap_type == "retention":
            f3_audio_instruction = "Focus on memory and retention. Create an audio script that reinforces learning through repetition and memory techniques."
        else:
            f3_audio_instruction = "Create an audio script that helps students understand and learn the topic."
        
        # F3: Add content requirements
        f3_requirements = []
        if content_requirements.get("storytelling"):
            f3_requirements.append("Include storytelling elements")
        if content_requirements.get("audio_engagement"):
            f3_requirements.append("Focus on audio engagement techniques")
        if content_requirements.get("interactive_elements"):
            f3_requirements.append("Include interactive elements")
        
        f3_requirements_text = f"F3 Requirements: {', '.join(f3_requirements)}" if f3_requirements else ""
        
        prompt = (
            f"Write a 60s audio script focused on fixing {gap_type} misconception(s): {focus}. "
            f"Gap Type: {gap_type}. Mode Coordination: {mode_coordination}. "
            f"{f3_audio_instruction} "
            f"{f3_requirements_text} "
            f"Include a short title, simple script, and 3 verbal checks tightly aligned to the gap. "
            f"Use context lightly if helpful (in_class_questions sample={str((context_bundle.get('in_class_questions') or [])[:1])}). "
            f"Return JSON with keys: title (optional), script (string), verbal_checks (list of 3). "
            f"Return only valid JSON."
        )
    else:
        prompt = (
            f"Write a 60s audio script about {topic} with a short title, story script, and 3 verbal checks. "
            f"If helpful, align with lesson_script excerpt={str(context_bundle.get('lesson_script'))[:120]}. "
            f"Return JSON with keys: title (optional), script (string), verbal_checks (list of 3). "
            f"Return only valid JSON."
        )
    
    print(f"🎧 [LISTENING_SPEAKING] Sending prompt to LLM...")
    content = await LLM.ainvoke(prompt)
    print(f"🎧 [LISTENING_SPEAKING] Received response from LLM")
    
    # Debug: Check what the LLM actually returned
    raw_content = content.content.strip() if content.content else ""
    print(f"🎧 [LISTENING_SPEAKING] Raw LLM response length: {len(raw_content)}")
    print(f"🎧 [LISTENING_SPEAKING] Raw LLM response preview: {raw_content[:200]}...")
    
    if not raw_content:
        print(f"❌ [LISTENING_SPEAKING] LLM returned empty response")
        payload = {
            "title": f"Audio about {topic}",
            "script": f"This is an audio script about {topic}. Listen carefully and think about what you learn.",
            "verbal_checks": ["What is the main topic?", "What did you learn?", "How can you apply this?"]
        }
        print(f"🎧 [LISTENING_SPEAKING] Using default fallback content")
    else:
        try:
            # Try to extract JSON from the response (in case it's wrapped in markdown)
            json_start = raw_content.find('{')
            json_end = raw_content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = raw_content[json_start:json_end]
                print(f"🎧 [LISTENING_SPEAKING] Extracted JSON content: {json_content[:200]}...")
                data = json.loads(json_content)
            else:
                # Try parsing the entire response as JSON
                data = json.loads(raw_content)
            
            print(f"🎧 [LISTENING_SPEAKING] Parsed JSON data successfully")
            validated = LearnByListeningSpeakingPayload(**data)
            print(f"🎧 [LISTENING_SPEAKING] Data validation passed")
            payload = validated.model_dump()
            await log_validation_result("AUDIO", True, None, {"verbal_checks": len(payload.get("verbal_checks", []))})
            print(f"🎧 [LISTENING_SPEAKING] Final payload prepared")
            
        except json.JSONDecodeError as e:
            print(f"❌ [LISTENING_SPEAKING] JSON decode error: {str(e)}")
            print(f"🎧 [LISTENING_SPEAKING] Raw content that failed to parse: {raw_content}")
            # Create a fallback payload with the raw content
            payload = {"script": raw_content, "verbal_checks": []}
            await log_validation_result("AUDIO", False, {"error": str(e)}, None)
            print(f"🎧 [LISTENING_SPEAKING] Using raw content as fallback")
            
        except Exception as e:
            print(f"❌ [LISTENING_SPEAKING] Error processing LLM response: {str(e)}")
            print(f"🎧 [LISTENING_SPEAKING] Raw content: {raw_content}")
            payload = {"script": raw_content, "verbal_checks": []}
            await log_validation_result("AUDIO", False, {"error": str(e)}, None)
            print(f"🎧 [LISTENING_SPEAKING] Using raw content as fallback")
    
    # Traceability
    job_id = None
    try:
        job_id = (getattr(config, "configurable", {}) or {}).get("thread_id")
    except Exception:
        job_id = None
    payload = {"_meta": {"mode": "AUDIO", "job_id": job_id}, **payload}

    print(f"🎧 [LISTENING_SPEAKING] Persisting artifact to database...")
    await persist_artifact(state.route, "AUDIO", payload, state.req)
    print(f"✅ [LISTENING_SPEAKING] Listening/Speaking node completed successfully")
    
    return {}
