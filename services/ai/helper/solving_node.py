import os
import json
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from services.ai.helper.utils import persist_artifact

# LLM (provider/model can be swapped)
LLM = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.2,
    google_api_key=os.environ["GEMINI_API_KEY"],
)

async def node_learn_by_solving(state, config: RunnableConfig) -> Dict[str, Any]:
    """
    Node for generating practice problems with progressive difficulty.
    """
    print(f"\n🧮 [SOLVING] Starting learn_by_solving node...")
    print(f"🧮 [SOLVING] Route: {state.route}")
    
    req = state.req
    topic = req.get("topic", "Topic")
    problem_opts = req.get("options", {}).get("problems", {})
    count = problem_opts.get("count", 4)
    preferred_types = problem_opts.get("types", ["MCQ", "FITB", "Short"])
    progressive_difficulty = problem_opts.get("progressive_difficulty", True)
    learning_gaps = req.get("learning_gaps") or []
    context_bundle = req.get("context_bundle") or {}
    gap_codes = []
    for g in learning_gaps:
        if isinstance(g, str):
            gap_codes.append(g)
        elif isinstance(g, dict) and g.get("code"):
            gap_codes.append(g["code"])

    print(f"🧮 [SOLVING] Topic: {topic}")
    print(f"🧮 [SOLVING] Problem count: {count}")
    print(f"🧮 [SOLVING] Problem types: {preferred_types}")
    print(f"🧮 [SOLVING] Progressive difficulty: {progressive_difficulty}")

    # Build context for better problem generation
    context_info = ""
    if context_bundle.get('in_class_questions'):
        context_info += f"Sample in-class questions: {str((context_bundle.get('in_class_questions') or [])[:2])}. "
    if context_bundle.get('lesson_script'):
        context_info += f"Lesson context: {str(context_bundle.get('lesson_script'))[:150]}. "

    if state.route == "REMEDY":
        focus = ", ".join(gap_codes) if gap_codes else topic
        prompt = (
            f"Create {count} problems tightly focused on fixing the misconception(s): {focus}. "
            f"Use these problem types: {', '.join(preferred_types)}. "
            f"Ensure progressive difficulty: start easy, end challenging. "
            f"{context_info}"
            f"Each problem must have: type, difficulty (easy/medium/hard), stem, options (for MCQ), answer, explanation. "
            f"Return JSON with key 'problems' as a list. "
            f"Add 'scheduling_hints' array with weak areas to resurface later."
        )
    else:
        prompt = (
            f"Create {count} problems for {topic} with progressive difficulty. "
            f"Use these problem types: {', '.join(preferred_types)}. "
            f"Ensure balanced difficulty distribution. "
            f"{context_info}"
            f"Each problem must have: type, difficulty (easy/medium/hard), stem, options (for MCQ), answer, explanation. "
            f"Return JSON with key 'problems' as a list. "
            f"Add 'scheduling_hints' array with weak areas to resurface later."
        )
    
    print(f"🧮 [SOLVING] Sending prompt to LLM...")
    content = await LLM.ainvoke(prompt)
    print(f"🧮 [SOLVING] Received response from LLM")

    raw_content = content.content.strip() if content.content else ""
    print(f"🧮 [SOLVING] Raw LLM response length: {len(raw_content)}")
    print(f"🧮 [SOLVING] Raw LLM response preview: {raw_content[:200]}...")

    if not raw_content:
        print(f"❌ [SOLVING] LLM returned empty response")
        payload = {"problems": []}
    else:
        try:
            json_start = raw_content.find('{')
            json_end = raw_content.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_content = raw_content[json_start:json_end]
                print(f"🧮 [SOLVING] Extracted JSON content: {json_content[:200]}...")
                data = json.loads(json_content)
            else:
                data = json.loads(raw_content)

            print(f"🧮 [SOLVING] Parsed JSON data successfully")
            # Accept flexible shape; ensure problems key exists
            if isinstance(data, dict):
                problems = data.get("problems", [])
                scheduling_hints = data.get("scheduling_hints", [])
                payload = {"problems": problems, "scheduling_hints": scheduling_hints}
            elif isinstance(data, list):
                payload = {"problems": data, "scheduling_hints": []}
            else:
                payload = {"problems": [data], "scheduling_hints": []}
            print(f"🧮 [SOLVING] Final payload prepared with {len(payload.get('problems', []))} problems and {len(payload.get('scheduling_hints', []))} scheduling hints")
        except json.JSONDecodeError as e:
            print(f"❌ [SOLVING] JSON decode error: {str(e)}")
            print(f"🧮 [SOLVING] Using raw content fallback")
            payload = {"problems": [raw_content] if raw_content else []}
        except Exception as e:
            print(f"❌ [SOLVING] Error processing LLM response: {str(e)}")
            payload = {"problems": [raw_content] if raw_content else []}
    
    # Traceability
    job_id = None
    try:
        job_id = (getattr(config, "configurable", {}) or {}).get("thread_id")
    except Exception:
        job_id = None
    payload = {"_meta": {"mode": "SOLVING", "job_id": job_id}, **payload}

    print(f"🧮 [SOLVING] Persisting artifact to database...")
    await persist_artifact(state.route, "SOLVING", payload, state.req)
    print(f"✅ [SOLVING] Solving node completed successfully")
    
    return {}
