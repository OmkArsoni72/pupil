import json
import base64
import os
import re
import google.generativeai as genai
from typing import Dict, Any, List
import logging
from datetime import datetime, time, timedelta, date
from bson import ObjectId
from fastapi import HTTPException


from pydantic import ValidationError

from core.models.timetable import PDFTimetable, TimetableEvent, TeacherInfo, Lesson
from core.services.db_operations.timetable_db import (
    create_timetable_events_in_db, 
    get_pdf_timetable_from_db, 
    get_unpaired_events_for_teacher,
    get_upcoming_sessions_for_class,
    get_events_for_teacher_class_day,
    pair_lesson_to_event,
    save_pdf_timetable_in_db,
    get_teachers_from_institution,
    get_timetable_event_by_id,
    update_timetable_event_status,
    move_session_to_completed
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
try:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    logger.error(f"Failed to configure Gemini: {e}")
    # You might want to handle this more gracefully, but for now, we log and proceed.
    # The app will fail later if a call to Gemini is made.


async def store_timetable_pdf(pdf_meta: PDFTimetable, pdf_content: bytes) -> str:
    """
    Encodes a PDF and saves it to the database along with its metadata.
    """
    encoded_pdf = base64.b64encode(pdf_content).decode('utf-8')
    pdf_meta.encoded_file = encoded_pdf
    inserted_id = await save_pdf_timetable_in_db(pdf_meta)
    return inserted_id

def _create_gemini_prompt(class_id: str, school_id: str, teachers: List[TeacherInfo]) -> str:
    """
    Creates a detailed, dynamic prompt for the Gemini API.
    """
    # Get the start of the current week (Monday)
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    
    # Serialize teacher data for inclusion in the prompt
    teachers_json_string = json.dumps([t.model_dump() for t in teachers])

    return f"""
You are an intelligent data extraction service for an education platform. Your task is to parse the provided school timetable PDF and convert it into a JSON array of timetable events.

**CRITICAL INSTRUCTION: Only extract timetable events for the class named "{class_id}". Ignore all other classes mentioned in the PDF.**

**Instructions:**
1. Analyze the timetable structure, which includes days, times, and subject/teacher names for class "{class_id}".
2. Use the provided data to create a JSON object for each class session belonging to "{class_id}".
3. Match the teacher's name from the timetable with a teacher in the provided `teachers` list. You MUST use the corresponding `teacher_id`.
**CRITICAL:** If a teacher's name found in the PDF does not exactly match any name in the `teachers` list, you MUST completely discard that class session and NOT include it in the final JSON output. Do not create an event with a missing or `null` `teacher_id`.
4. The `class_id` for all events is "{class_id}".
5. The `school_id` for all events is "{school_id}".
6. Calculate the `scheduled_date` for each event. The timetable is for the week starting {start_of_week.isoformat()}. Combine the date with the event's start time.
7. Calculate `duration_minutes` from the start and end times.
8. The output MUST be a valid JSON array. Each object must conform to the following schema:
    - `teacher_id`: string (use the ID from the list below)
    - `scheduled_date`: string (ISO 8601 format, e.g., "YYYY-MM-DDTHH:MM:SS")
    - `duration_minutes`: integer
    - `planned_lesson_id`: null
    - `event_type`: "class_session"
    - `status`: "scheduled"
    - `is_holiday`: false
    - `rescheduled_to_event_id`: null
    - `school_id`: "{school_id}"
    - `class_id`: "{class_id}"

**Provided Data:**
- `class_id`: "{class_id}"
- `school_id`: "{school_id}"
- `teachers`: {teachers_json_string}

Based on the PDF content and the data above, generate the JSON array. Ignore empty slots or non-class periods like "Assembly" or "Lunch".
"""


async def _parse_timetable_with_detailed_prompt(pdf_content: bytes, prompt: str) -> List[Dict[str, Any]]:

    """
    Sends the PDF and a detailed prompt to Gemini and gets structured data back.
    """
    logger.info("Sending request to Gemini API...")
    try:

        model = genai.GenerativeModel('gemini-2.0-flash')
        pdf_file_for_api = {
            'mime_type': 'application/pdf',
            'data': pdf_content
        }
        

        response = await model.generate_content_async([prompt, pdf_file_for_api])
        
        # Clean up the response and parse the JSON
        # The response might be wrapped in ```json ... ``` markdown.
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response.text)
        if json_match:
            json_string = json_match.group(1)
        else:
            # If no markdown block, assume the whole response is the JSON string
            json_string = response.text

        logger.info("Received and parsed response from Gemini.")
        return json.loads(json_string)

    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}", exc_info=True)
        # Re-raise as a ValueError to be caught by the route handler for a clean HTTP response.
        raise ValueError(f"An error occurred while communicating with the AI service: {e}")


async def ingest_timetable_from_db(class_id: str, school_id: str, academic_year: str):
    """
    Orchestrates the timetable ingestion by fetching a stored PDF and using an
    intelligent prompt to parse it.
    """
    logger.info(f"--- ENTERING TIMETABLE INGESTION for class '{class_id}' ---")
    try:
        # 1. Fetch the stored PDF and its metadata from DB
        logger.info("STEP 1: Fetching stored PDF from database...")
        pdf_timetable = await get_pdf_timetable_from_db(class_id, school_id, academic_year)
        logger.info("STEP 1: Successfully fetched PDF.")
        
        # 2. Fetch the latest teacher list for the school.
        logger.info(f"STEP 2: Fetching teacher list for school {pdf_timetable.school_id}...")
        teachers = await get_teachers_from_institution(pdf_timetable.school_id)
        logger.info("STEP 2: Successfully fetched teachers.")

        # 3. Decode PDF content
        logger.info("STEP 3: Decoding PDF content...")
        try:
            pdf_content = base64.b64decode(pdf_timetable.encoded_file)
            logger.info("STEP 3: Successfully decoded PDF.")
        except (base64.binascii.Error, TypeError) as e:
            logger.error(f"STEP 3 ERROR: Failed to decode PDF. Error: {e}")
            raise ValueError("Invalid base64 encoding for the stored PDF file.")

        # 4. Construct the detailed prompt using the fetched teacher list
        logger.info("STEP 4: Creating Gemini prompt...")
        gemini_prompt = _create_gemini_prompt(
            class_id=pdf_timetable.class_id,
            school_id=pdf_timetable.school_id,
            teachers=teachers
        )
        logger.info("STEP 4: Successfully created Gemini prompt.")

        # 5. Call Gemini to get structured, ready-to-insert data
        logger.info("STEP 5: Calling Gemini service for parsing...")

        parsed_events_json = await _parse_timetable_with_detailed_prompt(pdf_content, gemini_prompt)

        logger.info(f"STEP 5: Received {len(parsed_events_json)} events from Gemini.")
        
        if not parsed_events_json:
            raise ValueError("Gemini returned no events. Parsing might have failed.")

        # 6. Validate the data from Gemini against our Pydantic model
        logger.info("STEP 6: Validating parsed events...")
        events_to_create = []
        for i, event_data in enumerate(parsed_events_json):
            try:
                event_data['class_id'] = pdf_timetable.class_id
                event_data['school_id'] = pdf_timetable.school_id
                event = TimetableEvent(**event_data)
                events_to_create.append(event)
            except ValidationError as e:
                logger.warning(f"Skipping event #{i} from AI due to validation error: {e}.")
                continue
        logger.info(f"STEP 6: Successfully validated {len(events_to_create)} events.")
        
        if not events_to_create:
            raise ValueError("All parsed events failed validation. Check warning logs for details.")

        # 7. Save the validated events to the database
        logger.info("STEP 7: Saving events to database...")

        created_ids = await create_timetable_events_in_db(events_to_create)

        logger.info(f"STEP 7: Successfully created {len(created_ids)} timetable events in DB.")
        
        result = {
            "message": "Timetable ingested successfully from stored PDF.",
            "created_events_count": len(created_ids),
            "created_event_ids": [str(id) for id in created_ids],
        }
        logger.info(f"--- EXITING TIMETABLE INGESTION SUCCESSFULLY ---")
        return result

    except Exception as e:
        logger.error(f"--- UNHANDLED EXCEPTION in ingest_timetable_from_db: {type(e).__name__}: {e} ---", exc_info=True)
        # Re-raise the exception to be handled by the route
        raise 


async def pair_lessons_for_teacher(teacher_id: str):
    """
    Fetches all unpaired events for a teacher and pairs them with upcoming lesson sessions for each class.
    """
    logger.info(f"--- Starting lesson pairing process for teacher_id: {teacher_id} ---")

    # 1. Fetch all unpaired events for the teacher, sorted by date

    unpaired_events = await get_unpaired_events_for_teacher(teacher_id)
    if not unpaired_events:
        logger.info("No unpaired events found for this teacher.")
        return {"message": "No unpaired events found to process.", "paired_events_count": 0}

    # 2. Group events by class_id to handle each class's lesson sequence separately
    events_by_class = {}
    for event in unpaired_events:
        if event.class_id not in events_by_class:
            events_by_class[event.class_id] = []
        events_by_class[event.class_id].append(event)
    
    logger.info(f"Found {len(unpaired_events)} events across {len(events_by_class)} classes.")

    total_paired_count = 0
    pairing_details_by_class = {}

    # 3. For each class, fetch the upcoming sessions and pair them one by one
    for class_id, events in events_by_class.items():
        logger.info(f"Processing {len(events)} events for class_id: {class_id}")
        
        # Fetch the list of upcoming session IDs from the teacher_class_data collection.
        # The class_id from the event corresponds to the className in the content collection.

        sessions_to_pair = await get_upcoming_sessions_for_class(teacher_id, class_id)
        
        if not sessions_to_pair:
            logger.warning(f"No upcoming sessions found for class '{class_id}'. Skipping pairing for this class.")
            pairing_details_by_class[class_id] = "No upcoming sessions found to pair."
            continue

        paired_in_class = 0
        # The events are already sorted by date, and sessions are in sequence.
        for event, session_id in zip(events, sessions_to_pair):
            success = await pair_lesson_to_event(str(event.id), session_id)

            if success:
                paired_in_class += 1
        
        pairing_details_by_class[class_id] = f"{paired_in_class} sessions paired."
        total_paired_count += paired_in_class

    logger.info(f"--- Finished lesson pairing process. Total events paired: {total_paired_count} ---")
    return {
        "message": "Lesson pairing process completed.",
        "total_paired_events": total_paired_count,
        "details": pairing_details_by_class
    } 

def get_daily_schedule_for_teacher_class(teacher_id: str, class_id: str, day: date) -> List[TimetableEvent]:
    """
    Service function to fetch the daily schedule for a given teacher and class.
    """
    logger.info(f"Fetching schedule for teacher '{teacher_id}', class '{class_id}' on {day.isoformat()}")
    try:
        events = get_events_for_teacher_class_day(teacher_id, class_id, day)
        logger.info(f"Found {len(events)} events for the day.")
        return events
    except Exception as e:
        logger.error(f"Error in service layer while fetching daily schedule: {e}", exc_info=True)
        # Re-raise to be handled by the API layer
        raise 

async def complete_session_and_event(event_id: str) -> Dict[str, Any]:
    """
    Marks a session as complete by updating the event status and moving the session
    from 'upcoming' to 'completed' in the class curriculum data.
    """
    logger.info(f"--- Starting session completion process for event_id: {event_id} ---")

    # 1. Fetch the event to get necessary details
    event = await get_timetable_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Timetable event with id {event_id} not found.")

    if event.status == 'completed':
        logger.warning(f"Event {event_id} is already marked as completed.")
        return {"message": "Event was already completed.", "event_id": event_id}

    if not event.planned_lesson_id:
        raise HTTPException(status_code=400, detail="Cannot complete an event that has no planned lesson.")

    # 2. Update the event status to 'completed'
    status_updated = await update_timetable_event_status(event_id, 'completed')
    if not status_updated:
        # This is unlikely if the fetch succeeded, but good to handle.
        raise HTTPException(status_code=500, detail="Failed to update event status.")

    logger.info(f"Successfully updated status for event {event_id} to 'completed'.")

    # 3. Move the session from 'upcoming' to 'completed'
    session_moved = await move_session_to_completed(event.class_id, event.planned_lesson_id)
    if not session_moved:
        # This could happen if the session was already moved or the class document doesn't exist.
        logger.warning(f"Could not move session {event.planned_lesson_id} for class {event.class_id}. It might have been moved previously or the class data is missing.")
        # We don't raise an error here because the primary action (completing the event) succeeded.
        # This is a data consistency warning rather than a critical failure.

    logger.info(f"--- Session completion process finished for event_id: {event_id} ---")

    return {
        "message": "Session marked as complete successfully.",
        "event_id": event_id,
        "session_id": event.planned_lesson_id,
        "class_id": event.class_id
    } 