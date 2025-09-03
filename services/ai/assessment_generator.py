# services/ai/generate_assessment_graph.py
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from services.ai.schema_agent import SchemaAgent
from services.ai.context_agent import ContextAgent
from services.ai.question_generator import QuestionGenerator
from services.db_operations.assessment_db import save_assessment, update_job_status, mark_job_failed
from services.ai.llm_client import llm_factory
import uuid
import logging

logger = logging.getLogger(__name__)

class AssessmentState(TypedDict, total=False):
    # inputs
    target_exam: str
    exam_type: str
    previous_topics: list
    learning_gaps: list  # Added missing field
    difficulty: str
    subject: str
    class_: str  # Added missing field
    teacher_id: str  # Added missing field
    self_assessment_mode: str  # Added missing field
    file_url: str  # Added missing field
    llm_model: str
    job_id: str
    # intermediate / outputs
    schema: dict
    context: dict
    questions: list
    assessment_json: dict  # Raw assessment from LLM

async def generate_assessment(params: dict, job_id: str | None = None) -> str:
    """
    Build and run a LangGraph StateGraph to generate & save an assessment.
    Returns job_id.
    """
    if job_id is None:
        job_id = str(uuid.uuid4())
    await update_job_status(job_id, "pending")

    # initial state keys will be passed when invoking the compiled graph
    builder = StateGraph(AssessmentState)  # state schema type

    # Node: fetch schema/template from DB
    async def fetch_schema(state: AssessmentState) -> AssessmentState:
        print(f"🔍 [fetch_schema] Fetching template for: {state['target_exam']}")
        tpl = await SchemaAgent.fetch_template(state["target_exam"])
        print(f"✅ [fetch_schema] Template fetched: {tpl.get('target_exam', 'N/A') if tpl else 'None'}")
        return {"schema": tpl}

    # Node: gather context from DB
    async def gather_context(state: AssessmentState) -> AssessmentState:
        print(f"🔍 [gather_context] Gathering context for exam_type: {state.get('exam_type')}")
        ctx = await ContextAgent.gather_context(
            exam_type=state.get("exam_type"),
            previous_topics=state.get("previous_topics", []),
            learning_gaps=state.get("learning_gaps", []),
            file_url=state.get("file_url"),
            self_assessment_mode=state.get("self_assessment_mode"),
            subject=state.get("subject"),
            grade=int(state.get("class_", "10").replace("A", "").replace("B", "")) if state.get("class_") else None
        )
        print(f"✅ [gather_context] Context gathered - Topics: {len(ctx.get('selected_topics', []))}, Learning Outcomes: {len(ctx.get('learning_outcomes', []))}")
        return {"context": ctx}

    # Node: generate questions using provided LLM client
    async def generate_questions_node(state: AssessmentState) -> AssessmentState:
        print(f"🔍 [generate_questions] Starting question generation with LLM: {state.get('llm_model', 'gemini_1.5_flash')}")
        llm_client = llm_factory.get_client(state.get("llm_model", "gemini_1.5_flash"))
        assessment_json = await QuestionGenerator.generate_questions({
            "llm_client": llm_client,
            "schema": state.get("schema"),
            "context": state.get("context"),
            "difficulty": state.get("difficulty"),
            "subject": state.get("subject"),
        })
        
        print(f"📄 [generate_questions] Raw LLM response type: {type(assessment_json)}")
        print(f"📄 [generate_questions] Raw LLM response keys: {list(assessment_json.keys()) if isinstance(assessment_json, dict) else 'Not a dict'}")
        
        # If the generator returned an error, mark job failed and raise
        if isinstance(assessment_json, dict) and "error" in assessment_json:
            print(f"❌ [generate_questions] Error in LLM response: {assessment_json.get('error')}")
            await mark_job_failed(state.get("job_id") or job_id, assessment_json.get("error", "Unknown error"))
            raise RuntimeError(assessment_json.get("error", "Unknown error"))

        # Extract individual questions from the assessment JSON
        questions = extract_questions_from_assessment(assessment_json, state.get("context", {}))
        print(f"✅ [generate_questions] Extracted {len(questions)} questions from assessment")
        
        return {
            "assessment_json": assessment_json,
            "questions": questions
        }

    # Node: save result to DB (async)
    async def save_result(state: AssessmentState) -> AssessmentState:
        print(f"💾 [save_result] Saving {len(state.get('questions', []))} questions to database")
        # persist and mark job completed
        await save_assessment(state.get("questions"), state.get("job_id") or job_id, state)
        await update_job_status(state.get("job_id") or job_id, "completed")
        print(f"✅ [save_result] Assessment saved successfully with job_id: {state.get('job_id') or job_id}")
        return {}

    # Register nodes
    builder.add_node("fetch_schema", fetch_schema)
    builder.add_node("gather_context", gather_context)
    builder.add_node("generate_questions", generate_questions_node)
    builder.add_node("save_result", save_result)

    # Wire edges (start -> fetch_schema & gather_context -> generate_questions -> save_result -> END)
    builder.add_edge(START, "fetch_schema")
    builder.add_edge(START, "gather_context")
    builder.add_edge("fetch_schema", "generate_questions")
    builder.add_edge("gather_context", "generate_questions")
    builder.add_edge("generate_questions", "save_result")
    builder.add_edge("save_result", END)

    # Compile graph (returns CompiledStateGraph / runnable)
    compiled = builder.compile()

    # initial state for this run
    initial_state: AssessmentState = {
        "target_exam": params["target_exam"],
        "exam_type": params.get("exam_type"),
        "previous_topics": params.get("previous_topics", []),
        "learning_gaps": params.get("learning_gaps", []),
        "difficulty": params.get("difficulty"),
        "subject": params.get("subject"),
        "class_": params.get("class_"),
        "teacher_id": params.get("teacher_id"),
        "self_assessment_mode": params.get("self_assessment_mode"),
        "file_url": params.get("file_url"),
        "llm_model": params.get("llm_model"),
        "job_id": job_id,
    }

    # Run graph asynchronously and wait for completion
    try:
        await compiled.ainvoke(initial_state)
    except Exception as e:
        await mark_job_failed(job_id, str(e))
        raise

    return job_id

def extract_questions_from_assessment(assessment_json: dict, context: dict) -> list:
    """
    Extract individual questions from the assessment JSON and convert them to the proper format
    for saving to the question_bank collection.
    """
    print(f"🔍 [extract_questions] Starting extraction from assessment_json type: {type(assessment_json)}")
    questions = []
    
    # Handle error cases
    if isinstance(assessment_json, dict) and "error" in assessment_json:
        print(f"❌ [extract_questions] Assessment generation failed: {assessment_json.get('error')}")
        logger.error(f"Assessment generation failed: {assessment_json.get('error')}")
        return []
    
    # Extract questions from different possible structures
    if isinstance(assessment_json, dict):
        print(f"📄 [extract_questions] Assessment JSON keys: {list(assessment_json.keys())}")
        
        # Try to find questions in common assessment structures
        sections = assessment_json.get("sections", [])
        if not sections:
            sections = assessment_json.get("questions", [])
        if not sections:
            sections = [assessment_json]  # Treat the whole thing as one section
        
        print(f"📄 [extract_questions] Found {len(sections)} sections to process")
        
        for i, section in enumerate(sections):
            print(f"📄 [extract_questions] Processing section {i+1}: {type(section)}")
            if isinstance(section, dict):
                # Extract questions from section
                section_questions = section.get("questions", [])
                if not section_questions:
                    # Maybe the section itself is a question
                    if "questionText" in section or "question" in section:
                        section_questions = [section]
                
                print(f"📄 [extract_questions] Section {i+1} has {len(section_questions)} questions")
                
                for j, question in enumerate(section_questions):
                    print(f"📄 [extract_questions] Processing question {j+1}: {type(question)}")
                    if isinstance(question, dict):
                        print(f"📄 [extract_questions] Question {j+1} keys: {list(question.keys())}")
                        # Convert to proper question format matching question_bank schema
                        formatted_question = {
                            "questionText": question.get("questionText", question.get("question", "")),
                            "questionType": question.get("questionType", "MCQ"),
                            "origin": "ai_generated",
                            "options": _format_options(question.get("options", [])),
                            "answer": _format_answer(question.get("answer", {})),
                            "difficulty": question.get("difficulty", "medium"),
                            "grade": str(context.get("grade", "")),
                            "topics": context.get("selected_topics", []),
                            "learningOutcomes": context.get("learning_outcomes", []),
                            "usageHistory": [],
                            "statistics": {
                                "averageTimeSeconds": 0,
                                "successRate": 0.0,
                                "numberOfAttempts": 0
                            },
                            "setId": str(uuid.uuid4())  # Generate unique setId
                        }
                        questions.append(formatted_question)
                        print(f"✅ [extract_questions] Question {j+1} formatted successfully")
    
    print(f"✅ [extract_questions] Extracted {len(questions)} questions from assessment")
    logger.info(f"Extracted {len(questions)} questions from assessment")
    return questions

def _format_options(options: list) -> list:
    """Format options to match question_bank schema"""
    formatted = []
    for i, option in enumerate(options):
        if isinstance(option, str):
            formatted.append({"key": chr(65 + i), "text": option})
        elif isinstance(option, dict):
            formatted.append({
                "key": option.get("key", chr(65 + i)),
                "text": option.get("text", str(option))
            })
    return formatted

def _format_answer(answer: dict) -> dict:
    """Format answer to match question_bank schema"""
    if isinstance(answer, str):
        return {"key": answer, "explanation": ""}
    elif isinstance(answer, dict):
        return {
            "key": answer.get("key", answer.get("answer", "")),
            "explanation": answer.get("explanation", "")
        }
    return {"key": "", "explanation": ""}
