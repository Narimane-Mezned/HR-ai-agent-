from app.db.database import db_connection

def create_candidate(
    name: str, cv_text: str, created_by: str,
    applied_job_id: int = None, prescreening_answers: str = None, prescreening_flags: str = None,
    email: str = None, phone: str = None, linkedin_url: str = None, github_url: str = None,
) -> int:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO candidates
               (name, cv_text, created_by, applied_job_id, prescreening_answers, prescreening_flags,
                email, phone, linkedin_url, github_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, cv_text, created_by, applied_job_id, prescreening_answers, prescreening_flags,
             email, phone, linkedin_url, github_url),
        )
        conn.commit()
        return cursor.lastrowid


def get_candidate(candidate_id: int) -> dict | None:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def list_candidates(created_by: str) -> list[dict]:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidates WHERE created_by = ? ORDER BY created_at DESC", (created_by,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def update_candidate_cv(candidate_id: int, name: str, cv_text: str) -> bool:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE candidates SET name = ?, cv_text = ? WHERE id = ?", (name, cv_text, candidate_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_candidate(candidate_id: int) -> bool:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
        conn.commit()
        return cursor.rowcount > 0

def mark_candidate_hired(candidate_id: int, job_id: int, checklist_json: str) -> bool:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE candidates SET status = 'hired', hired_for_job_id = ?, onboarding_checklist = ? WHERE id = ?",
            (job_id, checklist_json, candidate_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def list_hired_candidates(created_by: str) -> list[dict]:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidates WHERE created_by = ? AND status = 'hired'", (created_by,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]