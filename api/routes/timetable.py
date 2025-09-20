from fastapi import APIRouter, UploadFile, File, Form, Body
from datetime import date
from api.controllers.timetable_controller import TimetableController, IngestionRequest, PairingRequest

router = APIRouter()

@router.post("/timetable/upload-pdf")
async def upload_timetable_pdf(
    file: UploadFile = File(...),
    class_id: str = Form(...),
    school_id: str = Form(...),
    academic_year: str = Form(...),
    generated_by_user_id: str = Form(...),
):
    """
    This endpoint accepts a timetable PDF and its metadata,
    encodes the PDF, and stores it in the database.
    The associated teacher list will be fetched from the 'institutions'
    collection during the ingestion process.
    """
    return await TimetableController.upload_timetable_pdf(
        file, class_id, school_id, academic_year, generated_by_user_id
    )

@router.post("/timetable/ingest-from-db")
async def ingest_timetable_from_database(request: IngestionRequest = Body(...)):
    """
    This endpoint fetches a stored timetable PDF from the database using a
    class_id, school_id, and academic_year, then processes it to create
    timetable events.
    """
    return await TimetableController.ingest_timetable_from_database(request)

@router.post("/timetable/pair-lessons")
async def pair_lessons_for_teacher_endpoint(request: PairingRequest = Body(...)):
    """
    This endpoint triggers the lesson pairing process for a specific teacher.
    It finds all their scheduled, unpaired class sessions and links them
    to the next available lessons for each class.
    """
    return await TimetableController.pair_lessons_for_teacher_endpoint(request)

@router.get("/timetable/daily-schedule")
async def get_daily_schedule(teacher_id: str, class_id: str, day: date):
    """
    Fetches the daily schedule for a specific teacher and class.
    The 'day' should be provided as a query parameter in YYYY-MM-DD format.
    """
    return await TimetableController.get_daily_schedule(teacher_id, class_id, day)

@router.post("/timetable/event/{event_id}/complete")
async def complete_timetable_event(event_id: str):
    """
    Marks a specific timetable event and its associated lesson as 'completed'.
    This action moves the session from 'upcoming' to 'completed' in the class data.
    """
    return await TimetableController.complete_timetable_event(event_id)