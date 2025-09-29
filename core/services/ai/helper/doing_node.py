import os
import json
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from core.services.ai.schemas import LearnByDoingPayload
from core.services.ai.helper.utils import persist_artifact, log_validation_result

# LLM (provider/model can be swapped)
LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
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
    
    # F3: Extract F3 orchestration specifications for gap-specific content
    f3_orchestration = context_bundle.get("f3_orchestration", {})
    gap_type = f3_orchestration.get("gap_type", "unknown")
    content_requirements = f3_orchestration.get("content_requirements", {}).get("doing", {})
    mode_coordination = f3_orchestration.get("mode_coordination", "")
    
    gap_codes = []
    for g in learning_gaps:
        if isinstance(g, str):
            gap_codes.append(g)
        elif isinstance(g, dict) and g.get("code"):
            gap_codes.append(g["code"])
    
    print(f"🔬 [DOING] Topic: {topic}")
    print(f"🔬 [DOING] F3: Gap type: {gap_type}, Mode coordination: {mode_coordination}")
    print(f"🔬 [DOING] F3: Content requirements: {content_requirements}")

    if state.route == "REMEDY":
        focus = ", ".join(gap_codes) if gap_codes else topic
        
        # F3: Build gap-specific activity instructions
        f3_activity_instruction = ""
        if gap_type == "conceptual":
            f3_activity_instruction = "Focus on conceptual understanding and relationships. Design hands-on experiments that help students understand underlying principles and conceptual relationships through direct experience."
        elif gap_type == "application":
            f3_activity_instruction = "Focus on practical application and real-world problem-solving. Design activities that require students to apply knowledge to solve practical, hands-on problems with real-world relevance."
        elif gap_type == "knowledge":
            f3_activity_instruction = "Focus on factual knowledge reinforcement. Design activities that help students remember and reinforce key facts and information through hands-on experience."
        elif gap_type == "foundational":
            f3_activity_instruction = "Focus on foundational knowledge building. Design activities that help students understand basic concepts and build strong foundations through simple, clear experiments."
        elif gap_type == "retention":
            f3_activity_instruction = "Focus on memory and retention. Design activities that reinforce learning through hands-on repetition and memory techniques."
        elif gap_type == "engagement":
            f3_activity_instruction = "Focus on engagement and motivation. Design fun, interactive activities that spark interest and encourage active participation through hands-on exploration."
        else:
            f3_activity_instruction = "Design hands-on activities that help students learn and understand the topic."
        
        # F3: Add content requirements
        f3_requirements = []
        if content_requirements.get("hands_on_experiments"):
            f3_requirements.append("Include hands-on experimental elements")
        if content_requirements.get("concept_application"):
            f3_requirements.append("Focus on concept application")
        if content_requirements.get("real_world_applications"):
            f3_requirements.append("Include real-world applications")
        if content_requirements.get("practical_exercises"):
            f3_requirements.append("Include practical exercises")
        
        f3_requirements_text = f"F3 Requirements: {', '.join(f3_requirements)}" if f3_requirements else ""
        
        prompt = (
            f"Design a very short, safe home activity to fix {gap_type} misconception(s): {focus}. "
            f"Gap Type: {gap_type}. Mode Coordination: {mode_coordination}. "
            f"{f3_activity_instruction} "
            f"{f3_requirements_text} "
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
