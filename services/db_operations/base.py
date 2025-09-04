import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
from bson.errors import InvalidId

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB Connection
client = AsyncIOMotorClient(MONGO_URI)
print("MongoDB connected:", MONGO_URI)

# Main DB (Atlas: 'Pupil_teach')
db = client["Pupil_teach"]

# === Collections (Unified) ===
user_collection = db["users"]
teacher_class_data_collection = db["teacher_class_data"]

timetable_events_collection = db["timetable_events"]
lessons_collection = db["lessons"]

pdf_timetable_collection = db["pdf_timetable"]
timetable_collection = db["timetable"]
institutions_collection = db["institutions"]

template_collection = db["templates"]
assessment_collection = db["assessments"]
questions_collection = db["question_bank"]
question_bank_collection=questions_collection
lesson_script_collection = db["lesson_script"]

sessions_collection = db["sessions"]
student_reports_collection = db["student_reports"]
class_reports_collection = db["class_reports"]
jobs_collection = db["jobs"]

# Optional legacy aliases
flashcard_users_collection = db["users"]  # from flashcard_game
teacher_timeline_lessons_collection = db["lessons"]

# === Async Helper Functions ===

async def get_student_report(student_id: str, class_id: str):
    report = await student_reports_collection.find_one({"studentId": student_id, "classId": class_id})
    if report and "_id" in report:
        report["_id"] = str(report["_id"])
    return report


async def get_class_report_by_board_grade_section(board: str, grade: str, section: str):
    report = await class_reports_collection.find_one({"board": board, "grade": grade, "section": section})
    all_reports = await class_reports_collection.find().to_list(length=None)
    print("All class reports:", all_reports)
    print("Fetched class report:", report)
    if report and "_id" in report:
        report["_id"] = str(report["_id"])
    return report


async def get_all_chapters_from_teacher_class_data(class_id: str):
    doc = await teacher_class_data_collection.find_one({"classId": ObjectId(class_id)})
    if not doc:
        return None
    curriculum = doc.get("curriculum", {})
    return curriculum.get("chapters", [])


async def update_chapters_in_teacher_class_data(class_id: str, chapters: list):
    result = await teacher_class_data_collection.update_one(
        {"classId": ObjectId(class_id)},
        {"$set": {"curriculum.chapters": chapters}}
    )
    return result.modified_count > 0


async def get_chapter_content(class_id: str, chapter_id: str):
    class_doc = await teacher_class_data_collection.find_one({"classId": ObjectId(class_id)})
    if not class_doc:
        return None

    chapters = class_doc.get("curriculum", {}).get("chapters", [])
    target_chapter = next((c for c in chapters if c.get("chapterId") == chapter_id), None)
    if not target_chapter:
        return None

    chapter_sessions = target_chapter.get("chapterSessions", [])
    if not chapter_sessions:
        return []

    session_queries = [
        {"chapterId": chapter_id, "lessonNumber": s.get("lessonNumber")}
        for s in chapter_sessions if s.get("lessonNumber") is not None
    ]

    if not session_queries:
        return []

    sessions = await sessions_collection.find({"$or": session_queries}).to_list(length=None)

    content = []
    for session in sessions:
        session_content = {"sessionId": str(session.get("_id"))}
        if "lessonScript" in session:
            session_content["lessonScript"] = session["lessonScript"]
        if "inClassQuestions" in session:
            session_content["inClassQuestions"] = session["inClassQuestions"]

        if len(session_content) > 1:
            content.append(session_content)

    return content


async def get_after_hour_session_content(session_id: str):
    query = {}
    try:
        query["_id"] = ObjectId(session_id)
    except InvalidId:
        query["_id"] = session_id

    session = await sessions_collection.find_one(query)
    return session.get("afterHourSession") if session and "afterHourSession" in session else None


async def get_lesson_content(session_id: str):
    query = {}
    try:
        query["_id"] = ObjectId(session_id)
    except InvalidId:
        query["_id"] = session_id

    session = await sessions_collection.find_one(query)
    if not session:
        return None

    content = {}
    if "lessonScript" in session:
        content["lessonScript"] = session["lessonScript"]
    if "inClassQuestions" in session:
        content["inClassQuestions"] = session["inClassQuestions"]

    return content if content else None


async def update_after_hour_session(session_id: str, content: dict):
    query = {}
    try:
        query["_id"] = ObjectId(session_id)
    except InvalidId:
        query["_id"] = session_id

    result = await sessions_collection.update_one(query, {"$set": {"afterHourSession": content}})
    return result.modified_count > 0


async def update_lesson_script(session_id: str, content: dict):
    query = {}
    try:
        query["_id"] = ObjectId(session_id)
    except InvalidId:
        query["_id"] = session_id

    result = await sessions_collection.update_one(query, {"$set": {"lessonScript": content}})
    return result.modified_count > 0


async def update_in_class_questions(session_id: str, content: dict):
    query = {}
    try:
        query["_id"] = ObjectId(session_id)
    except InvalidId:
        query["_id"] = session_id

    result = await sessions_collection.update_one(query, {"$set": {"inClassQuestions": content}})
    return result.modified_count > 0
