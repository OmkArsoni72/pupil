import os
import json
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from core.services.ai.schemas import LearnByWritingPayload
from core.services.ai.helper.utils import persist_artifact, log_validation_result

# LLM (provider/model can be swapped)
LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    google_api_key=os.environ["GEMINI_API_KEY"],
)

async def node_learn_by_writing(state, config: RunnableConfig) -> Dict[str, Any]:
    """
    Node for generating writing prompts to assess recall and understanding.
    AHS-only per PRD; silently skip if Remedies.
    """
    print(f"\n✍️ [WRITING] Starting learn_by_writing node...")
    print(f"✍️ [WRITING] Route: {state.route}")
    
    # AHS-only per PRD; silently skip if Remedies
    if state.route != "AHS":
        print(f"⏭️ [WRITING] Skipping - not AHS route")
        return {}
    
    topic = state.req.get("topic")
    learning_gaps = state.req.get("learning_gaps") or []
    context_bundle = state.req.get("context_bundle") or {}
    gap_codes = []
    for g in learning_gaps:
        if isinstance(g, str):
            gap_codes.append(g)
        elif isinstance(g, dict) and g.get("code"):
            gap_codes.append(g["code"])
    print(f"✍️ [WRITING] Topic: {topic}")

    prompt = (
        f"Generate a JSON with key 'prompts' as a list of 2-4 open-ended prompts to assess recall & understanding on: {topic}. "
        f"Condition on context if useful: lesson_script excerpt={str(context_bundle.get('lesson_script'))[:160]}, "
        f"in_class_questions_sample={str((context_bundle.get('in_class_questions') or [])[:2])}. "
        f"Return only valid JSON."
    )
    
    print(f"✍️ [WRITING] Sending prompt to LLM...")
    content = await LLM.ainvoke(prompt)
    print(f"✍️ [WRITING] Received response from LLM")
    
    # Debug: Check what the LLM actually returned
    raw_content = content.content.strip() if content.content else ""
    print(f"✍️ [WRITING] Raw LLM response length: {len(raw_content)}")
    print(f"✍️ [WRITING] Raw LLM response preview: {raw_content[:200]}...")
    
    if not raw_content:
        print(f"❌ [WRITING] LLM returned empty response")
        payload = {"prompts": ["Please explain what you learned about " + topic]}
        print(f"✍️ [WRITING] Using default fallback prompt")
    else:
        try:
            # Try to extract JSON from the response (in case it's wrapped in markdown)
            json_start = raw_content.find('{')
            json_end = raw_content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = raw_content[json_start:json_end]
                print(f"✍️ [WRITING] Extracted JSON content: {json_content[:200]}...")
                data = json.loads(json_content)
            else:
                # Try parsing the entire response as JSON
                data = json.loads(raw_content)
            
            print(f"✍️ [WRITING] Parsed JSON data successfully")
            validated = LearnByWritingPayload(**data)
            print(f"✍️ [WRITING] Data validation passed")
            payload = validated.model_dump()
            await log_validation_result("WRITING", True, None, {"prompts": len(payload.get("prompts", []))})
            print(f"✍️ [WRITING] Final payload prepared: {payload}")
            
        except json.JSONDecodeError as e:
            print(f"❌ [WRITING] JSON decode error: {str(e)}")
            print(f"✍️ [WRITING] Raw content that failed to parse: {raw_content}")
            # Create a fallback payload with the raw content as a single prompt
            payload = {"prompts": [raw_content if raw_content else f"Explain what you learned about {topic}"]}
            await log_validation_result("WRITING", False, {"error": str(e)}, None)
            print(f"✍️ [WRITING] Using raw content as fallback")
            
        except Exception as e:
            print(f"❌ [WRITING] Error processing LLM response: {str(e)}")
            print(f"✍️ [WRITING] Raw content: {raw_content}")
            payload = {"prompts": [raw_content if raw_content else f"Explain what you learned about {topic}"]}
            print(f"✍️ [WRITING] Using raw content as fallback")
    
    # Traceability
    job_id = None
    try:
        job_id = (getattr(config, "configurable", {}) or {}).get("thread_id")
    except Exception:
        job_id = None
    payload = {"_meta": {"mode": "WRITING", "job_id": job_id}, **payload}

    print(f"✍️ [WRITING] Persisting artifact to database...")
    await persist_artifact(state.route, "WRITING", payload, state.req)
    print(f"✅ [WRITING] Writing node completed successfully")
    
    return {}
