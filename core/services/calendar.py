
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/calendar"]
SERVICE_ACCOUNT_FILE = "credentials.json"

# Initialize calendar service only if credentials file exists
service = None
credentials = None

def _initialize_calendar_service():
    """Initialize calendar service if credentials are available."""
    global service, credentials
    if service is None and os.path.exists(SERVICE_ACCOUNT_FILE):
        try:
            credentials = Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )
            service = build("calendar", "v3", credentials=credentials)
        except Exception as e:
            print(f"Warning: Could not initialize calendar service: {e}")
            service = False  # Mark as failed to avoid repeated attempts
    return service

def _get_calendar_service():
    """Get calendar service, initializing if needed."""
    if service is None:
        _initialize_calendar_service()
    return service if service is not False else None

async def create_event(calendar_id, lecture):
    """Create a calendar event. Returns None if calendar service is unavailable."""
    calendar_service = _get_calendar_service()
    if calendar_service is None:
        print("Warning: Calendar service not available, skipping event creation")
        return None

    try:
        event = {
            'summary': lecture.topic,
            'start': {'dateTime': lecture.start_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
            'end': {'dateTime': lecture.end_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
        }
        created_event = calendar_service.events().insert(calendarId=calendar_id, body=event).execute()
        return created_event.get('id')
    except Exception as e:
        print(f"Warning: Failed to create calendar event: {e}")
        return None

async def delete_event(event_id):
    """Delete a calendar event. Does nothing if calendar service is unavailable."""
    calendar_service = _get_calendar_service()
    if calendar_service is None:
        print("Warning: Calendar service not available, skipping event deletion")
        return

    try:
        calendar_service.events().delete(calendarId='primary', eventId=event_id).execute()
    except Exception as e:
        print(f"Warning: Failed to delete calendar event: {e}")
        # Don't raise exception, just log the warning
