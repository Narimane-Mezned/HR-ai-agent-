import os
import datetime
from zoneinfo import ZoneInfo
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.config import APP_TIMEZONE

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]
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


def _parse_google_datetime(dt_str: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


def get_free_slots(
    duration_minutes: int = 30,
    business_start_hour: int = 9,
    business_end_hour: int = 17,
    days_ahead: int = 7,
    max_slots: int = 3,
) -> list[str]:
    tz = ZoneInfo(APP_TIMEZONE)
    now = datetime.datetime.now(tz)
    window_start = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    window_end = window_start + datetime.timedelta(days=days_ahead)

    service = get_calendar_service()
    freebusy_result = service.freebusy().query(body={
        "timeMin": window_start.isoformat(),
        "timeMax": window_end.isoformat(),
        "timeZone": APP_TIMEZONE,
        "items": [{"id": "primary"}],
    }).execute()

    busy_periods = [
        (_parse_google_datetime(b["start"]), _parse_google_datetime(b["end"]))
        for b in freebusy_result["calendars"]["primary"]["busy"]
    ]

    free_slots = []
    day_cursor = window_start
    while day_cursor < window_end and len(free_slots) < max_slots:
        if day_cursor.weekday() < 5:
            slot_start = day_cursor.replace(hour=business_start_hour, minute=0)
            day_end = day_cursor.replace(hour=business_end_hour, minute=0)
            while slot_start + datetime.timedelta(minutes=duration_minutes) <= day_end and len(free_slots) < max_slots:
                slot_end = slot_start + datetime.timedelta(minutes=duration_minutes)
                overlaps = any(slot_start < b_end and slot_end > b_start for b_start, b_end in busy_periods)
                if not overlaps:
                    free_slots.append(slot_start.isoformat())
                    slot_start += datetime.timedelta(hours=1)
                else:
                    slot_start += datetime.timedelta(minutes=30)
        day_cursor += datetime.timedelta(days=1)

    return free_slots


def create_calendar_event(candidate_name: str, candidate_email: str, job_title: str, start_iso: str, duration_minutes: int = 30) -> dict:
   
    service = get_calendar_service()

    start_dt = datetime.datetime.fromisoformat(start_iso)
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=ZoneInfo(APP_TIMEZONE))
    end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)

    event_body = {
        "summary": f"Interview: {candidate_name} — {job_title}",
        "description": f"Interview for the {job_title} position with {candidate_name}.",
        "start": {"dateTime": start_dt.isoformat(), "timeZone": APP_TIMEZONE},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": APP_TIMEZONE},
        "visibility": "private",
        "attendees": [{"email": candidate_email}] if candidate_email else [],
    }

    created_event = service.events().insert(calendarId="primary", body=event_body, sendUpdates="all").execute()
    return {"event_id": created_event["id"], "html_link": created_event.get("htmlLink")}