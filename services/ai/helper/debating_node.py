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

async def node_learn_by_questioning_debating(state, config: RunnableConfig) -> Dict[str, Any]:
    """
    Node for generating Socratic debate setups and questioning frameworks.
    """
    print(f"\n💭 [DEBATING] Starting learn_by_questioning_debating node...")
    print(f"💭 [DEBATING] Route: {state.route}")
    print(f"💭 [DEBATING] Topic: {state.req.get('topic', 'N/A')}")
    
    context_bundle = state.req.get("context_bundle") or {}
    topic = state.req.get('topic', 'the topic')
    learning_gaps = state.req.get("learning_gaps") or []
    gap_codes = []
    for g in learning_gaps:
        if isinstance(g, str):
            gap_codes.append(g)
        elif isinstance(g, dict) and g.get("code"):
            gap_codes.append(g["code"])
    
    if state.route == "REMEDY":
        focus = ", ".join(gap_codes) if gap_codes else topic
        prompt = (
            f"Create a debate setup in JSON with keys: settings, personas, prompts, closing_summary_cue. "
            f"Focus on fixing the misconception(s): {focus}. "
            f"Use context if helpful (lesson_script excerpt={str(context_bundle.get('lesson_script'))[:120]}). "
            "Settings should include format and simple rules. Personas should include a teacher-like guide and a student. "
            "Prompts should be Socratic questions that help correct the misconception."
        )
    else:
        prompt = (
            "Create a debate setup in JSON with keys: settings, personas, prompts, closing_summary_cue. "
            f"Topic: {topic}. "
            f"Use context lightly if helpful (lesson_script excerpt={str(context_bundle.get('lesson_script'))[:120]}). "
            "Settings should include format and simple rules. Personas should include a teacher-like guide and a student."
        )
    
    print(f"💭 [DEBATING] Sending prompt to LLM...")
    content = await LLM.ainvoke(prompt)
    print(f"💭 [DEBATING] Received response from LLM")
    
    # Debug: Check what the LLM actually returned
    raw_content = content.content.strip() if content.content else ""
    print(f"💭 [DEBATING] Raw LLM response length: {len(raw_content)}")
    print(f"💭 [DEBATING] Raw LLM response preview: {raw_content[:200]}...")
    
    if not raw_content:
        print(f"❌ [DEBATING] LLM returned empty response")
        payload = {
            "settings": {"topic": topic, "format": "discussion", "rules": ["Be respectful", "Listen actively"]},
            "personas": {"teacher": "Guide", "student": "Learner"},
            "prompts": ["What do you think about this?", "Can you explain further?"],
            "closing_summary_cue": "Summarize what we discussed"
        }
        print(f"💭 [DEBATING] Using default fallback content")
    else:
        try:
            # Try to extract JSON from the response (in case it's wrapped in markdown)
            json_start = raw_content.find('{')
            json_end = raw_content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = raw_content[json_start:json_end]
                print(f"💭 [DEBATING] Extracted JSON content: {json_content[:200]}...")
                data = json.loads(json_content)
            else:
                # Try parsing the entire response as JSON
                data = json.loads(raw_content)
            
            print(f"💭 [DEBATING] Parsed JSON data successfully")
            # Ensure required keys exist
            required_keys = ["settings", "personas", "prompts", "closing_summary_cue"]
            for key in required_keys:
                if key not in data:
                    data[key] = {}
            payload = data
            print(f"💭 [DEBATING] Final payload prepared")
            
        except json.JSONDecodeError as e:
            print(f"❌ [DEBATING] JSON decode error: {str(e)}")
            print(f"💭 [DEBATING] Raw content that failed to parse: {raw_content}")
            # Create a fallback payload with the raw content
            payload = {"raw_debate": raw_content}
            print(f"💭 [DEBATING] Using raw content as fallback")
            
        except Exception as e:
            print(f"❌ [DEBATING] Error processing LLM response: {str(e)}")
            print(f"💭 [DEBATING] Raw content: {raw_content}")
            payload = {"raw_debate": raw_content}
            print(f"💭 [DEBATING] Using raw content as fallback")
    
    # Traceability
    job_id = None
    try:
        job_id = (getattr(config, "configurable", {}) or {}).get("thread_id")
    except Exception:
        job_id = None
    payload = {"_meta": {"mode": "DEBATING", "job_id": job_id}, **payload}

    print(f"💭 [DEBATING] Persisting artifact to database...")
    await persist_artifact(state.route, "DEBATING", payload, state.req)
    print(f"✅ [DEBATING] Debating node completed successfully")
    
    return {}
