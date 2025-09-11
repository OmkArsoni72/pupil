import os
import json
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from services.ai.schemas import LearnByListeningSpeakingPayload
from services.ai.helper.utils import persist_artifact, log_validation_result

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
    gap_codes = []
    for g in learning_gaps:
        if isinstance(g, str):
            gap_codes.append(g)
        elif isinstance(g, dict) and g.get('code'):
            gap_codes.append(g['code'])
    
    if state.route == 'REMEDY':
        focus = ", ".join(gap_codes) if gap_codes else topic
        prompt = (
            f"Write a 60s audio script focused on fixing the student's misconception(s): {focus}. "
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
