import os
import json
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from core.services.ai.helper.utils import persist_artifact, log_validation_result

# LLM (provider/model can be swapped)
LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
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
    options = req.get("options") or {}
    problem_opts = options.get("problems", {})
    count = problem_opts.get("count", 4)
    preferred_types = problem_opts.get("types", ["MCQ", "FITB", "Short"])
    progressive_difficulty = problem_opts.get("progressive_difficulty", True)
    learning_gaps = req.get("learning_gaps") or []
    context_bundle = req.get("context_bundle") or {}
    
    # F3: Extract F3 orchestration specifications for gap-specific content
    f3_orchestration = context_bundle.get("f3_orchestration", {})
    gap_type = f3_orchestration.get("gap_type", "unknown")
    content_requirements = f3_orchestration.get("content_requirements", {}).get("solving", {})
    mode_coordination = f3_orchestration.get("mode_coordination", "")
    
    gap_codes = []
    for g in learning_gaps:
        if isinstance(g, str):
            gap_codes.append(g)
        elif isinstance(g, dict) and g.get("code"):
            gap_codes.append(g["code"])
    
    print(f"🧮 [SOLVING] F3: Gap type: {gap_type}, Mode coordination: {mode_coordination}")
    print(f"🧮 [SOLVING] F3: Content requirements: {content_requirements}")

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
        
        # F3: Build gap-specific problem generation instructions
        f3_problem_instruction = ""
        if gap_type == "application":
            f3_problem_instruction = "Focus on practical application and real-world problem-solving. Create problems that require students to apply knowledge to solve practical, hands-on problems. Include step-by-step solutions and real-world scenarios."
        elif gap_type == "conceptual":
            f3_problem_instruction = "Focus on conceptual understanding and relationships. Create problems that test understanding of concepts, relationships, and underlying principles."
        elif gap_type == "knowledge":
            f3_problem_instruction = "Focus on factual knowledge and information recall. Create problems that test knowledge of facts, terms, and basic information."
        elif gap_type == "foundational":
            f3_problem_instruction = "Focus on foundational knowledge and prerequisites. Create problems that test basic concepts and foundational understanding."
        elif gap_type == "retention":
            f3_problem_instruction = "Focus on memory and retention. Create problems that reinforce learning through spaced repetition and memory techniques."
        elif gap_type == "engagement":
            f3_problem_instruction = "Focus on engagement and motivation. Create problems that are interesting, interactive, and encourage active participation."
        else:
            f3_problem_instruction = "Create problems that help students practice and apply their knowledge."
        
        # F3: Add content requirements
        f3_requirements = []
        if content_requirements.get("progressive_difficulty"):
            f3_requirements.append("Ensure progressive difficulty from easy to challenging")
        if content_requirements.get("step_by_step_solutions"):
            f3_requirements.append("Include detailed step-by-step solutions")
        if content_requirements.get("spaced_repetition"):
            f3_requirements.append("Include spaced repetition techniques")
        if content_requirements.get("memory_reinforcement"):
            f3_requirements.append("Include memory reinforcement strategies")
        
        f3_requirements_text = f"F3 Requirements: {', '.join(f3_requirements)}" if f3_requirements else ""
        
        prompt = (
            f"Create {count} problems tightly focused on fixing {gap_type} misconception(s): {focus}. "
            f"Gap Type: {gap_type}. Mode Coordination: {mode_coordination}. "
            f"{f3_problem_instruction} "
            f"{f3_requirements_text} "
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
    # Validate structure
    try:
        from core.services.ai.schemas import LearnBySolvingPayload
        _ = LearnBySolvingPayload(**payload | {k: v for k, v in payload.items() if k in ("problems", "scheduling_hints", "difficulty")})
        await log_validation_result("SOLVING", True, None, {"problems": len(payload.get("problems", []))})
    except Exception as e:
        await log_validation_result("SOLVING", False, {"error": str(e)}, None)

    print(f"🧮 [SOLVING] Persisting artifact to database...")
    await persist_artifact(state.route, "SOLVING", payload, state.req)
    print(f"✅ [SOLVING] Solving node completed successfully")
    
    return {}
