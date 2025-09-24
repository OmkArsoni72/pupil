"""
Question Generation Node - Generates questions using LLM.
Extracted from services/ai/assessment_generator.py
"""

from typing import Dict, Any
from services.ai.question_generator import QuestionGenerator
from services.ai.llm_client import llm_factory
from services.db_operations.assessment_db import mark_job_failed
import uuid


async def question_generation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate questions using provided LLM client."""
    print(f"🔍 [question_generation_node] Starting question generation with LLM: {state.get('llm_model', 'gemini_1.5_flash')}")
    
    try:
        llm_client = llm_factory.get_client(state.get("llm_model", "gemini_1.5_flash"))
        assessment_json = await QuestionGenerator.generate_questions({
            "llm_client": llm_client,
            "schema": state.get("schema"),
            "context": state.get("context"),
            "difficulty": state.get("difficulty"),
            "subject": state.get("subject"),
        })
        
        print(f"📄 [question_generation_node] Raw LLM response type: {type(assessment_json)}")
        print(f"📄 [question_generation_node] Raw LLM response keys: {list(assessment_json.keys()) if isinstance(assessment_json, dict) else 'Not a dict'}")
        
        # If the generator returned an error, mark job failed and raise
        if isinstance(assessment_json, dict) and "error" in assessment_json:
            print(f"❌ [question_generation_node] Error in LLM response: {assessment_json.get('error')}")
            await mark_job_failed(state.get("job_id"), assessment_json.get("error", "Unknown error"))
            raise RuntimeError(assessment_json.get("error", "Unknown error"))

        # Extract individual questions from the assessment JSON
        questions = extract_questions_from_assessment(assessment_json, state.get("context", {}))
        print(f"✅ [question_generation_node] Extracted {len(questions)} questions from assessment")
        
        return {
            "assessment_json": assessment_json,
            "questions": questions
        }
        
    except Exception as e:
        print(f"❌ [question_generation_node] Error during question generation: {str(e)}")
        await mark_job_failed(state.get("job_id"), f"Question generation failed: {str(e)}")
        raise RuntimeError(f"Question generation failed: {str(e)}")


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
