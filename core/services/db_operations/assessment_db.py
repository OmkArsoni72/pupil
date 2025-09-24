from services.db_operations.base import (
    template_collection,
    assessment_collection,
    questions_collection,
    lesson_script_collection
)
from datetime import datetime
from bson import ObjectId
from typing import List
import requests
import tempfile
import os

try:
    from langchain_community.document_loaders import UnstructuredPDFLoader, UnstructuredWordDocumentLoader
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "langchain_community is missing. Install with: pip install -U langchain-community"
    )

# Templates
def get_templates_collection():
    return template_collection

async def get_template_by_target_exam(target_exam: str) -> dict | None:
    template = await template_collection.find_one({"target_exam": target_exam})
    if template:
        template["_id"] = str(template["_id"])
    return template

# Assessments
async def save_assessment(questions: list, job_id: str, params: dict = None):
    print(f"💾 [save_assessment] Starting to save assessment with {len(questions)} questions")
    # First save individual questions to get their IDs
    question_ids = await save_questions_to_db(questions, job_id=job_id)
    print(f"💾 [save_assessment] Saved {len(question_ids)} questions to question_bank")
    
    assessment_doc = {
        "job_id": job_id,
        "status": "completed",
        "created_at": datetime.utcnow(),
        "question_ids": question_ids,
        "request_params": params or {}
    }
    print(f"💾 [save_assessment] Assessment document prepared: {assessment_doc}")
    
    # Update existing job doc instead of inserting a duplicate
    result = await assessment_collection.update_one(
        {"job_id": job_id},
        {"$set": assessment_doc},
        upsert=True
    )
    print(f"✅ [save_assessment] Assessment saved to DB - matched: {result.matched_count}, modified: {result.modified_count}")

    # Fetch assessment to get its _id and associate back to questions
    assessment = await assessment_collection.find_one({"job_id": job_id})
    if assessment and assessment.get("_id"):
        assessment_id_str = str(assessment["_id"])
        print(f"🔗 [save_assessment] Associating questions with assessment_id: {assessment_id_str}")
        await associate_questions_with_assessment(question_ids, assessment_id_str, job_id)
    else:
        print(f"⚠️ [save_assessment] Could not fetch assessment _id for job_id: {job_id}")
    return job_id

async def save_questions_to_db(questions: list, job_id: str | None = None) -> List[str]:
    """Save individual questions to question_bank collection and return their IDs"""
    print(f"💾 [save_questions_to_db] Starting to save {len(questions)} questions")
    question_ids = []
    
    for i, question in enumerate(questions):
        print(f"💾 [save_questions_to_db] Processing question {i+1}: {question.get('questionText', '')[:50]}...")
        # Prepare question document for question_bank collection
        question_doc = {
            "questionText": question.get("questionText", ""),
            "questionType": question.get("questionType", "MCQ"),
            "origin": "ai_generated",
            "options": question.get("options", []),
            "answer": question.get("answer", {}),
            "difficulty": question.get("difficulty", "medium"),
            "grade": question.get("grade", ""),
            "topics": question.get("topics", []),
            "learningOutcomes": question.get("learningOutcomes", []),
            "usageHistory": [],
            "statistics": {
                "averageTimeSeconds": 0,
                "successRate": 0.0,
                "numberOfAttempts": 0
            },
            "setId": str(ObjectId()),  # Generate a unique setId
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "assessment_job_id": job_id
        }
        
        print(f"💾 [save_questions_to_db] Question {i+1} document prepared: {question_doc}")
        
        result = await questions_collection.insert_one(question_doc)
        question_ids.append(str(result.inserted_id))
        print(f"✅ [save_questions_to_db] Question {i+1} saved with ID: {result.inserted_id}")
    
    print(f"✅ [save_questions_to_db] All {len(question_ids)} questions saved successfully")
    return question_ids

async def associate_questions_with_assessment(question_ids: List[str], assessment_id: str, job_id: str):
    """Back-link questions to the assessment and append usageHistory."""
    print(f"🔗 [associate_q_to_assessment] Linking {len(question_ids)} questions to assessment {assessment_id}")
    object_ids = [ObjectId(qid) for qid in question_ids]
    usage_record = {
        "setId": assessment_id,
        "setType": "assessment",
        "dateUsed": datetime.utcnow().isoformat()
    }
    result = await questions_collection.update_many(
        {"_id": {"$in": object_ids}},
        {
            "$set": {"updated_at": datetime.utcnow()},
            "$addToSet": {"assessmentIds": assessment_id},
            "$push": {"usageHistory": usage_record}
        }
    )
    print(f"✅ [associate_q_to_assessment] Updated {result.modified_count} question docs with assessment link")

async def update_job_status(job_id: str, status: str):
    await assessment_collection.update_one(
        {"job_id": job_id}, {"$set": {"status": status}}, upsert=True
    )

async def mark_job_failed(job_id: str, error: str):
    await assessment_collection.update_one(
        {"job_id": job_id},
        {"$set": {"status": "failed", "error": error, "updated_at": datetime.utcnow()}},
        upsert=True
    )

async def get_assessment_by_job_id(job_id: str) -> dict | None:
    assessment = await assessment_collection.find_one({"job_id": job_id})
    if assessment:
        assessment["_id"] = str(assessment["_id"])
        assessment["question_ids"] = [str(qid) for qid in assessment.get("question_ids", [])]
    return assessment

async def get_assessment_by_id(assessment_id: str) -> dict | None:
    assessment = await assessment_collection.find_one({"_id": ObjectId(assessment_id)})
    if assessment:
        assessment["_id"] = str(assessment["_id"])
        assessment["question_ids"] = [str(qid) for qid in assessment.get("question_ids", [])]
    return assessment

# Questions
async def get_questions_by_ids(question_ids: List[str]) -> List[dict]:
    object_ids = [ObjectId(qid) if not isinstance(qid, ObjectId) else qid for qid in question_ids]
    cursor = questions_collection.find({"_id": {"$in": object_ids}})
    questions = await cursor.to_list(length=len(object_ids))
    for q in questions:
        q["_id"] = str(q["_id"])
    return questions

async def get_pyq_examples(topics: List[str], limit: int = 5, difficulty: str = None, question_types: List[str] = None) -> List[dict]:
    """
    Fetch relevant PYQ examples based on topics, difficulty, and question types.
    Prioritizes questions that match the assessment requirements.
    """
    # Build query based on available filters
    query = {"topics": {"$in": topics}}
    
    if difficulty:
        query["difficulty"] = difficulty
    
    if question_types:
        query["questionType"] = {"$in": question_types}
    
    # Use aggregation to get diverse examples
    pipeline = [
        {"$match": query},
        {"$sample": {"size": limit * 2}},  # Get more to filter
        {"$sort": {"statistics.numberOfAttempts": -1}},  # Prioritize well-used questions
        {"$limit": limit}
    ]
    
    cursor = questions_collection.aggregate(pipeline)
    examples = await cursor.to_list(length=limit)
    
    # Convert ObjectIds to strings
    for ex in examples:
        ex["_id"] = str(ex["_id"])
    
    return examples

def download_and_parse_file(file_url: str) -> List[dict]:
    _, ext = os.path.splitext(file_url)
    ext = ext.lower()

    response = requests.get(file_url)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
        tmp_file.write(response.content)
        tmp_filepath = tmp_file.name

    try:
        if ext == ".pdf":
            loader = UnstructuredPDFLoader(tmp_filepath)
        elif ext in [".docx", ".doc"]:
            loader = UnstructuredWordDocumentLoader(tmp_filepath)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        documents = loader.load()
    finally:
        os.remove(tmp_filepath)

    return documents

async def get_topics_by_date_range(start_date, end_date, subject: str = None, grade: int = None):
    """
    Get topics covered in lesson_script within a date range.
    Since lesson_script doesn't have date fields, we'll return all topics for now.
    In a real implementation, you'd need to add date tracking to lesson_script.
    """
    # For now, return all topics from lesson_script
    # This is a simplified implementation - in production you'd want date tracking
    pipeline = []
    
    if subject:
        pipeline.append({"$match": {"subjects.name": subject}})
    if grade:
        pipeline.append({"$match": {"grade": grade}})
    
    pipeline.extend([
        {"$unwind": "$sections"},
        {"$unwind": "$sections.subjects"},
        {"$unwind": "$sections.subjects.chapters"},
        {"$project": {
            "topic": "$sections.subjects.chapters.name",
            "subject": "$sections.subjects.name",
            "grade": "$grade"
        }}
    ])
    
    cursor = lesson_script_collection.aggregate(pipeline)
    topics = await cursor.to_list(None)
    return [topic["topic"] for topic in topics]

async def get_random_past_topics(limit: int = 5, subject: str = None, grade: int = None):
    """
    Get random topics from lesson_script.
    Since we don't have learning_gaps, we'll use learning outcomes from lesson_script.
    """
    pipeline = []
    
    if subject:
        pipeline.append({"$match": {"subjects.name": subject}})
    if grade:
        pipeline.append({"$match": {"grade": grade}})
    
    pipeline.extend([
        {"$unwind": "$sections"},
        {"$unwind": "$sections.subjects"},
        {"$unwind": "$sections.subjects.chapters"},
        {"$project": {
            "topic": "$sections.subjects.chapters.name",
            "subject": "$sections.subjects.name",
            "grade": "$grade"
        }},
        {"$sample": {"size": limit}}
    ])
    
    cursor = lesson_script_collection.aggregate(pipeline)
    topics = await cursor.to_list(None)
    return [topic["topic"] for topic in topics]

async def get_learning_outcomes_by_topics(topics: List[str]) -> List[str]:
    """
    Get learning outcomes for given topics from lesson_script.
    """
    pipeline = [
        {"$unwind": "$sections"},
        {"$unwind": "$sections.subjects"},
        {"$unwind": "$sections.subjects.chapters"},
        {"$match": {"sections.subjects.chapters.name": {"$in": topics}}},
        {"$project": {
            "learningOutcomes": "$sections.subjects.chapters.learningOutcomes",
            "topic": "$sections.subjects.chapters.name"
        }}
    ]
    
    cursor = lesson_script_collection.aggregate(pipeline)
    results = await cursor.to_list(None)
    
    learning_outcomes = []
    for result in results:
        if result.get("learningOutcomes"):
            learning_outcomes.extend(result["learningOutcomes"])
    
    return list(set(learning_outcomes))  # Remove duplicates
