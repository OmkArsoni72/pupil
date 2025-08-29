from typing import List
from pymongo.errors import PyMongoError
from fastapi import HTTPException
from bson.errors import InvalidId
import logging
from datetime import datetime, time, date

from models.timetable import PDFTimetable, TimetableEvent, TeacherInfo
from services.db_operations.base import pdf_timetable_collection, timetable_collection, institutions_collection, teacher_class_data_collection
from bson import ObjectId

logger = logging.getLogger(__name__)

def get_pdf_timetable_from_db(class_id: str, school_id: str, academic_year: str) -> PDFTimetable:
    """
    Fetches a single PDF timetable document from the database.
    """
    try:
        pdf_data = pdf_timetable_collection.find_one({
            "class_id": class_id,
            "school_id": school_id,
            "academic_year": academic_year
        })
        if not pdf_data:
            raise HTTPException(status_code=404, detail="PDF timetable not found for the given criteria.")
        
        return PDFTimetable(**pdf_data)
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def create_timetable_events_in_db(events: List[TimetableEvent]) -> List[str]:
    """
    Inserts multiple timetable events into the database.
    """
    try:
        # Pydantic models need to be converted to dicts for MongoDB driver.
        # Using `exclude_none=True` prevents `_id: null` from being inserted,
        # which allows MongoDB to generate a unique ObjectId for each new event.
        event_docs = [event.model_dump(by_alias=True, exclude_none=True) for event in events]
        result = timetable_collection.insert_many(event_docs)
        return [str(inserted_id) for inserted_id in result.inserted_ids]
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error while creating timetable events: {str(e)}")

def save_pdf_timetable_in_db(pdf_meta: PDFTimetable) -> str:
    """
    Saves a PDF timetable's metadata and encoded content to the database.
    """
    try:
        # Use exclude_none=True to prevent `_id: null` from being inserted.
        pdf_data = pdf_meta.model_dump(by_alias=True, exclude_none=True)
        result = pdf_timetable_collection.insert_one(pdf_data)
        return str(result.inserted_id)
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error while saving PDF timetable: {str(e)}")

def get_unpaired_events_for_teacher(teacher_id: str) -> List[TimetableEvent]:
    """Fetches all scheduled events for a teacher that don't have a lesson paired yet, sorted by date."""
    try:
        events_cursor = timetable_collection.find({
            "teacher_id": teacher_id,
            "planned_lesson_id": None,
            "is_holiday": False,
            "status": "scheduled"
        }).sort("scheduled_date", 1)
        return [TimetableEvent(**event) for event in events_cursor]
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error while fetching events: {str(e)}")

def get_upcoming_sessions_for_class(teacher_id: str, class_name: str) -> List[str]:
    """
    Fetches the list of upcoming session IDs for a specific teacher and class.
    """
    try:
        # We need to match the teacherId and the className.
        # The teacherId in the document is stored as an ObjectId.
        teacher_class_data = teacher_class_data_collection.find_one({
            "teacherId": teacher_id,
            "className": class_name
        })

        if not teacher_class_data:
            logger.warning(f"No teacher_class_data found for teacher '{teacher_id}' and class '{class_name}'.")
            return []
        
        # The session IDs are stored under sessions -> upcoming.
        upcoming_sessions = teacher_class_data.get("sessions", {}).get("upcoming", [])
        
        if not upcoming_sessions:
            logger.warning(f"No upcoming sessions found for teacher '{teacher_id}' and class '{class_name}'.")

        return upcoming_sessions
    except PyMongoError as e:
        logger.error(f"Database error fetching upcoming sessions for teacher {teacher_id}: {e}")
        # We return an empty list and let the service layer decide how to handle it.
        return []

def get_events_for_teacher_class_day(teacher_id: str, class_id: str, day: date) -> List[TimetableEvent]:
    """Fetches all scheduled events for a specific teacher, class, and day, sorted by time."""
    try:
        start_of_day = datetime.combine(day, time.min)
        end_of_day = datetime.combine(day, time.max)

        events_cursor = timetable_collection.find({
            "teacher_id": teacher_id,
            "class_id": class_id,
            "scheduled_date": {
                "$gte": start_of_day,
                "$lte": end_of_day
            }
        }).sort("scheduled_date", 1)
        
        return [TimetableEvent(**event) for event in events_cursor]
    except PyMongoError as e:
        logger.error(f"Database error while fetching events for teacher {teacher_id} on {day}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error while fetching events: {str(e)}")

def pair_lesson_to_event(event_id: str, lesson_id: str) -> bool:
    """Updates a timetable event to link it to a specific lesson."""
    try:
        result = timetable_collection.update_one(
            {"_id": ObjectId(event_id)},
            {"$set": {"planned_lesson_id": lesson_id}}
        )
        if result.matched_count == 0:
            logger.warning(f"Pairing failed: Event with id {event_id} not found.")
            return False
        return True
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error while pairing lesson to event: {str(e)}")

def get_teachers_from_institution(school_id: str) -> List[TeacherInfo]:
    """
    Fetches the list of teachers for a given school from the institutions collection.
    """
    try:
        institution = institutions_collection.find_one({"_id": ObjectId(school_id)})
        
        if not institution:
            logger.warning(f"Institution with school_id '{school_id}' not found.")
            raise HTTPException(status_code=404, detail=f"Institution with school_id '{school_id}' not found.")
        
        teacher_data = institution.get("teachers", [])
        if not teacher_data:
            logger.warning(f"Institution with school_id '{school_id}' has no teachers listed.")
            raise HTTPException(status_code=404, detail=f"No teachers found for institution '{school_id}'.")

        teachers = [
            TeacherInfo(teacher_id=str(teacher['id']), name=teacher['name'])
            for teacher in teacher_data
        ]
        return teachers
    except InvalidId:
        logger.error(f"Invalid school_id format: {school_id}")
        raise HTTPException(status_code=400, detail=f"Invalid school_id format: {school_id}")
    except PyMongoError as e:
        logger.error(f"Database error while fetching teachers for school {school_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") 