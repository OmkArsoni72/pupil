import os
import json
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from services.ai.schemas import LearnByDoingPayload
from services.ai.helper.utils import persist_artifact, log_validation_result

# LLM (provider/model can be swapped)
LLM = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.2,
    google_api_key=os.environ["GEMINI_API_KEY"],
)

async def node_learn_by_doing(state, config: RunnableConfig) -> Dict[str, Any]:
    """
    Node for generating safe home experiments and hands-on activities.
    """
    print(f"\n🔬 [DOING] Starting learn_by_doing node...")
    print(f"🔬 [DOING] Route: {state.route}")
    
    topic = state.req.get("topic", "Topic")
    learning_gaps = state.req.get("learning_gaps") or []
    context_bundle = state.req.get("context_bundle") or {}
    gap_codes = []
    for g in learning_gaps:
        if isinstance(g, str):
            gap_codes.append(g)
        elif isinstance(g, dict) and g.get("code"):
            gap_codes.append(g["code"])
    print(f"🔬 [DOING] Topic: {topic}")

    if state.route == "REMEDY":
        focus = ", ".join(gap_codes) if gap_codes else topic
        prompt = (
            f"Design a very short, safe home activity to fix the misconception(s): {focus}. "
            f"Use context if helpful (script excerpt={str(context_bundle.get('lesson_script'))[:120]}). "
            f"Return JSON with keys: materials (list), steps (list), post_task_questions (list), safety_notes (list), evaluation_criteria (list). "
            f"Safety notes must include specific precautions. Evaluation criteria should assess understanding and safety. "
            f"Return only valid JSON."
        )
    else:
        prompt = (
            f"Design a safe home experiment for {topic} and return JSON with keys: "
            f"materials (list), steps (list), post_task_questions (list), safety_notes (list), evaluation_criteria (list). "
            f"Consider grade-level constraints and simple household materials. "
            f"Safety notes must include specific precautions. Evaluation criteria should assess understanding and safety. "
            f"Return only valid JSON."
        )
    
    print(f"🔬 [DOING] Sending prompt to LLM...")
    content = await LLM.ainvoke(prompt)
    print(f"🔬 [DOING] Received response from LLM")
    
    # Debug: Check what the LLM actually returned
    raw_content = content.content.strip() if content.content else ""
    print(f"🔬 [DOING] Raw LLM response length: {len(raw_content)}")
    print(f"🔬 [DOING] Raw LLM response preview: {raw_content[:200]}...")
    
    if not raw_content:
        print(f"❌ [DOING] LLM returned empty response")
        payload = {
            "materials": ["Basic materials for " + topic],
            "steps": ["Step 1: Prepare materials", "Step 2: Follow safety guidelines", "Step 3: Conduct experiment"],
            "post_task_questions": ["What did you observe?", "What did you learn?"],
            "safety_notes": ["Always follow safety guidelines", "Have adult supervision if needed"],
            "evaluation_criteria": ["Student demonstrates understanding of the concept", "Student follows safety procedures correctly"]
        }
        print(f"🔬 [DOING] Using default fallback content")
    else:
        try:
            # Try to extract JSON from the response (in case it's wrapped in markdown)
            json_start = raw_content.find('{')
            json_end = raw_content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = raw_content[json_start:json_end]
                print(f"🔬 [DOING] Extracted JSON content: {json_content[:200]}...")
                data = json.loads(json_content)
            else:
                # Try parsing the entire response as JSON
                data = json.loads(raw_content)
            
            print(f"🔬 [DOING] Parsed JSON data successfully")
            validated = LearnByDoingPayload(**data)
            print(f"🔬 [DOING] Data validation passed")
            payload = validated.model_dump()
            await log_validation_result("DOING", True, None, {"steps": len(payload.get("steps", []))})
            print(f"🔬 [DOING] Final payload prepared")
            
        except json.JSONDecodeError as e:
            print(f"❌ [DOING] JSON decode error: {str(e)}")
            print(f"🔬 [DOING] Raw content that failed to parse: {raw_content}")
            # Create a fallback payload with the raw content
            payload = {"raw": raw_content}
            await log_validation_result("DOING", False, {"error": str(e)}, None)
            print(f"🔬 [DOING] Using raw content as fallback")
            
        except Exception as e:
            print(f"❌ [DOING] Error processing LLM response: {str(e)}")
            print(f"🔬 [DOING] Raw content: {raw_content}")
            payload = {"raw": raw_content}
            await log_validation_result("DOING", False, {"error": str(e)}, None)
            print(f"🔬 [DOING] Using raw content as fallback")
    
    # Traceability
    job_id = None
    try:
        job_id = (getattr(config, "configurable", {}) or {}).get("thread_id")
    except Exception:
        job_id = None
    payload = {"_meta": {"mode": "DOING", "job_id": job_id}, **payload}

    print(f"🔬 [DOING] Persisting artifact to database...")
    await persist_artifact(state.route, "DOING", payload, state.req)
    print(f"✅ [DOING] Doing node completed successfully")
    
    return {}
