import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
TOKEN_PATH = "token.json"
CREDENTIALS_PATH = "credentials.json"


def get_calendar_service():
   
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def create_calendar_event(candidate_name: str, candidate_email: str, job_title: str, start_iso: str, duration_minutes: int = 30) -> dict:
   
    service = get_calendar_service()

    start_dt = datetime.datetime.fromisoformat(start_iso)
    end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)

    event_body = {
        "summary": f"Interview: {candidate_name} — {job_title}",
        "description": f"Interview for the {job_title} position with {candidate_name}.",
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": "UTC"},
        "visibility": "private",
        "attendees": [{"email": candidate_email}] if candidate_email else [],
    }

    created_event = service.events().insert(calendarId="primary", body=event_body, sendUpdates="all").execute()
    return {"event_id": created_event["id"], "html_link": created_event.get("htmlLink")}