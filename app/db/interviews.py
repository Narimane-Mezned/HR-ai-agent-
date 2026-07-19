from app.db.database import get_connection


def init_interviews_table() -> None:
    conn = get_connection()
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
    conn.close()

def create_interview(candidate_id: int, job_id: int, confirmed_time: str, created_by: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO interviews (candidate_id, job_id, confirmed_time, created_by) VALUES (?, ?, ?, ?)",
        (candidate_id, job_id, confirmed_time, created_by.strip()),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def list_interviews_for_hr(created_by: str) -> list[dict]:
  
    conn = get_connection()
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
    conn.close()
    return [dict(row) for row in rows]