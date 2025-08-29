import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
from bson.errors import InvalidId

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
MONGODB_URL = os.getenv("MONGODB_URL")

# MongoDB Connection
client = AsyncIOMotorClient(MONGO_URI)
print('MongoDB URL:'+ MONGO_URI)
db = client["Pupil_teach"]
user_collection = db["users"]
teacher_class_data_collection = db["teacher_class_data"]

timetable_events_collection = db["timetable_events"]
lessons_collection = db["lessons"]



pdf_timetable_collection = db["pdf_timetable"]
timetable_collection = db["timetable"]
institutions_collection = db["institutions"]

template_collection= db['templates']
assessment_collection=db['assessments']
questions_collection=db['question_bank']
lesson_script_collection = db['lesson_script']

async def get_student_report(student_id: str, class_id: str):
    report = await db["student_reports"].find_one({"studentId": student_id, "classId": class_id})
    if report and "_id" in report:
        report["_id"] = str(report["_id"])
    return report


async def get_class_report_by_board_grade_section(board: str, grade: str, section: str):
    report = await db["class_reports"].find_one({"board": board, "grade": grade, "section": section})
    all_reports = await db["class_reports"].find().to_list(length=None)
    print('All class reports:', all_reports)
    print('Fetched class report:', report)
    if report and "_id" in report:
        report["_id"] = str(report["_id"])
    return report

async def get_all_chapters_from_teacher_class_data(class_id: str):
    """
    Finds the curriculum document using the classId and returns all its chapters.
    """
    doc = await teacher_class_data_collection.find_one({"classId": ObjectId(class_id)})
    if not doc:
        return None
    curriculum = doc.get("curriculum", {})
    return curriculum.get("chapters", [])

async def update_chapters_in_teacher_class_data(class_id: str, chapters: list):
    """
    Finds the curriculum document using the classId and updates its chapters.
    """
    result = await teacher_class_data_collection.update_one(
        {"classId": ObjectId(class_id)},
        {"$set": {"curriculum.chapters": chapters}}
    )
    return result.modified_count > 0

async def get_chapter_content(class_id: str, chapter_id: str):
    """
    Finds the curriculum document using the classId to fetch content for a specific chapter.
    """
    # Find the curriculum document using the new classId reference
    class_doc = await db.teacher_class_data.find_one({"classId": ObjectId(class_id)})
    if not class_doc:
        return None

    # Find the specific chapter within the curriculum
    chapters = class_doc.get("curriculum", {}).get("chapters", [])
    target_chapter = None
    for chapter in chapters:
        if chapter.get("chapterId") == chapter_id:
            target_chapter = chapter
            break

    if not target_chapter:
        return None  # Chapter not found

    # Get session identifiers (lesson numbers) from the chapter
    chapter_sessions = target_chapter.get("chapterSessions", [])
    if not chapter_sessions:
        return []

    # Build a query to fetch all relevant sessions using chapterId and lessonNumber
    session_queries = [
        {"chapterId": chapter_id, "lessonNumber": s.get("lessonNumber")}
        for s in chapter_sessions if s.get("lessonNumber") is not None
    ]

    if not session_queries:
        return []

    # Fetch all sessions corresponding to the lesson numbers for this chapter
    sessions_cursor = db.sessions.find({"$or": session_queries})
    sessions = await sessions_cursor.to_list(length=None)

    # Extract lesson scripts and in-class questions
    content = []
    for session in sessions:
        session_content = {
            "sessionId": str(session.get("_id"))
        }
        if "lessonScript" in session:
            session_content["lessonScript"] = session["lessonScript"]
        if "inClassQuestions" in session:
            session_content["inClassQuestions"] = session["inClassQuestions"]
        
        # Only add to the list if there is actual content
        if "lessonScript" in session_content or "inClassQuestions" in session_content:
            content.append(session_content)

    return content

async def get_after_hour_session_content(session_id: str):
    """
    Fetches the after-hour session content for a given session ID.
    """
    query = {}
    try:
        # Try to convert to ObjectId, if it fails, use the raw string.
        query["_id"] = ObjectId(session_id)
    except InvalidId:
        query["_id"] = session_id

    session = await db.sessions.find_one(query)

    if session and "afterHourSession" in session:
        return session["afterHourSession"]
    return None


async def get_lesson_content(session_id: str):
    """
    Fetches the lesson script and in-class questions for a given session ID.
    """
    query = {}
    try:
        # Try to convert to ObjectId, if it fails, use the raw string.
        query["_id"] = ObjectId(session_id)
    except InvalidId:
        query["_id"] = session_id

    session = await db.sessions.find_one(query)

    if not session:
        return None

    content = {}
    if "lessonScript" in session:
        content["lessonScript"] = session["lessonScript"]
    if "inClassQuestions" in session:
        content["inClassQuestions"] = session["inClassQuestions"]

    return content if content else None


async def update_after_hour_session(session_id: str, content: dict):
    """
    Updates the after-hour session content for a given session ID.
    """
    query = {}
    try:
        query["_id"] = ObjectId(session_id)
    except InvalidId:
        query["_id"] = session_id
    
    result = await db.sessions.update_one(query, {"$set": {"afterHourSession": content}})
    return result.modified_count > 0


async def update_lesson_script(session_id: str, content: dict):
    """
    Updates the lesson script for a given session ID.
    """
    query = {}
    try:
        query["_id"] = ObjectId(session_id)
    except InvalidId:
        query["_id"] = session_id
        
    result = await db.sessions.update_one(query, {"$set": {"lessonScript": content}})
    return result.modified_count > 0


async def update_in_class_questions(session_id: str, content: dict):
    """
    Updates the in-class questions for a given session ID.
    """
    query = {}
    try:
        query["_id"] = ObjectId(session_id)
    except InvalidId:
        query["_id"] = session_id

    result = await db.sessions.update_one(query, {"$set": {"inClassQuestions": content}})
    return result.modified_count > 0
