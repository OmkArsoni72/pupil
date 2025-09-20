import json
from fastapi import HTTPException, UploadFile, File, Form, Body
from pydantic import BaseModel
from datetime import date
import logging
from bson import ObjectId

from services.timetable_service import (
    ingest_timetable_from_db,
    pair_lessons_for_teacher,
    store_timetable_pdf,
    get_daily_schedule_for_teacher_class,
    complete_session_and_event
)
from services.db_operations.timetable_db import get_teachers_from_institution
from models.timetable import PDFTimetable, TeacherInfo

logger = logging.getLogger(__name__)


class IngestionRequest(BaseModel):
    class_id: str
    school_id: str
    academic_year: str


class PairingRequest(BaseModel):
    teacher_id: str


class TimetableController:
    """
    Controller for timetable operations.
    Handles PDF upload, ingestion, lesson pairing, scheduling, and event completion.
    """

    @staticmethod
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
        if file.content_type != 'application/pdf':
            raise HTTPException(status_code=400, detail="Invalid file type. Only PDF is accepted.")

        try:
            pdf_meta = PDFTimetable(
                class_id=class_id,
                school_id=school_id,
                academic_year=academic_year,
                generated_by_user_id=generated_by_user_id,
                file_name=file.filename,
                encoded_file="placeholder"  # This will be replaced by the service
            )
            # Use the asynchronous file read method
            pdf_content = await file.read()

            inserted_id = await store_timetable_pdf(pdf_meta, pdf_content)

            return {"message": "PDF timetable uploaded successfully", "id": str(inserted_id)}
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            print(f"Error uploading timetable PDF: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred during PDF upload.")

    @staticmethod
    async def ingest_timetable_from_database(request: IngestionRequest = Body(...)):
        """
        This endpoint fetches a stored timetable PDF from the database using a
        class_id, school_id, and academic_year, then processes it to create
        timetable events.
        """
        try:
            result = await ingest_timetable_from_db(
                class_id=request.class_id,
                school_id=request.school_id,
                academic_year=request.academic_year
            )
            return result
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            print(f"Error processing timetable from DB: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred during timetable processing.")

    @staticmethod
    async def pair_lessons_for_teacher_endpoint(request: PairingRequest = Body(...)):
        """
        This endpoint triggers the lesson pairing process for a specific teacher.
        It finds all their scheduled, unpaired class sessions and links them
        to the next available lessons for each class.
        """
        try:
            result = await pair_lessons_for_teacher(request.teacher_id)
            return result
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Error during lesson pairing for teacher {request.teacher_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="An unexpected error occurred during the lesson pairing process.")

    @staticmethod
    async def get_daily_schedule(teacher_id: str, class_id: str, day: date):
        """
        Fetches the daily schedule for a specific teacher and class.
        The 'day' should be provided as a query parameter in YYYY-MM-DD format.
        """
        try:
            daily_events = await get_daily_schedule_for_teacher_class(teacher_id, class_id, day)
            return daily_events
        except HTTPException as http_exc:
            # Re-raise known HTTP exceptions directly
            raise http_exc
        except Exception as e:
            logger.error(f"Error fetching daily schedule for teacher {teacher_id} on {day}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching the daily schedule.")

    @staticmethod
    async def complete_timetable_event(event_id: str):
        """
        Marks a specific timetable event and its associated lesson as 'completed'.
        This action moves the session from 'upcoming' to 'completed' in the class data.
        """
        try:
            if not ObjectId.is_valid(event_id):
                raise HTTPException(status_code=400, detail="Invalid event_id format.")

            result = await complete_session_and_event(event_id)
            return result
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Error during event completion for event_id {event_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="An unexpected error occurred during the event completion process.")