

SCOPES = ["https://www.googleapis.com/auth/calendar"]
SERVICE_ACCOUNT_FILE = "credentials.json"

credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("calendar", "v3", credentials=credentials)

async def create_event(calendar_id, lecture):
    event = {
        'summary': lecture.topic,
        'start': {'dateTime': lecture.start_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': lecture.end_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
    }
    created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
    return created_event.get('id')

async def delete_event(event_id):
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
    except Exception as e:
        raise Exception(f"Failed to delete event: {str(e)}")
