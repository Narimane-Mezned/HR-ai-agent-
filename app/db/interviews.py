import datetime
from zoneinfo import ZoneInfo
from app.db.database import db_connection
from app.config import APP_TIMEZONE


def init_interviews_table() -> None:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL,
                confirmed_time TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates(id),
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            )
        """)
        conn.commit()

def create_interview(candidate_id: int, job_id: int, confirmed_time: str, created_by: str) -> int:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO interviews (candidate_id, job_id, confirmed_time, created_by) VALUES (?, ?, ?, ?)",
            (candidate_id, job_id, confirmed_time, created_by.strip()),
        )
        conn.commit()
        return cursor.lastrowid

def list_interviews_for_hr(created_by: str) -> list[dict]:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT interviews.*, candidates.name AS candidate_name, jobs.title AS job_title
            FROM interviews
            JOIN candidates ON interviews.candidate_id = candidates.id
            JOIN jobs ON interviews.job_id = jobs.id
            WHERE interviews.created_by = ?
            ORDER BY interviews.confirmed_time ASC
            """,
            (created_by,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def list_interviews_today(created_by: str) -> list[dict]:
    tz = ZoneInfo(APP_TIMEZONE)
    today = datetime.datetime.now(tz).date()

    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT interviews.*, candidates.name AS candidate_name, jobs.title AS job_title
            FROM interviews
            JOIN candidates ON interviews.candidate_id = candidates.id
            JOIN jobs ON interviews.job_id = jobs.id
            WHERE interviews.created_by = ?
            """,
            (created_by,),
        )
        rows = [dict(row) for row in cursor.fetchall()]

    todays = []
    for row in rows:
        try:
            confirmed_dt = datetime.datetime.fromisoformat(row["confirmed_time"])
        except (ValueError, TypeError):
            continue
        if confirmed_dt.tzinfo is None:
            confirmed_dt = confirmed_dt.replace(tzinfo=tz)
        if confirmed_dt.astimezone(tz).date() == today:
            todays.append(row)

    todays.sort(key=lambda r: r["confirmed_time"])
    return todays