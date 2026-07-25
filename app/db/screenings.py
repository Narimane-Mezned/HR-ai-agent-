import json
from app.db.database import get_connection


def save_screening(candidate_id: int, job_id: int, result: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO screenings
            (candidate_id, job_id, score, verdict, justification, category, skills, years_experience)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(candidate_id, job_id) DO UPDATE SET
            score = excluded.score,
            verdict = excluded.verdict,
            justification = excluded.justification,
            category = excluded.category,
            skills = excluded.skills,
            years_experience = excluded.years_experience,
            created_at = CURRENT_TIMESTAMP
        """,
        (
            candidate_id, job_id,
            result.get("score"), result.get("verdict"), result.get("justification"),
            result.get("category"), json.dumps(result.get("skills", [])), result.get("years_experience"),
        ),
    )
    conn.commit()

    cursor.execute("SELECT id FROM screenings WHERE candidate_id = ? AND job_id = ?", (candidate_id, job_id))
    row_id = cursor.fetchone()["id"]
    conn.close()
    return row_id


def list_screenings_for_job(job_id: int) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT screenings.*, candidates.name AS candidate_name
        FROM screenings
        JOIN candidates ON screenings.candidate_id = candidates.id
        WHERE screenings.job_id = ?
        ORDER BY screenings.score DESC
        """,
        (job_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_screenings_for_candidate(candidate_id: int) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM screenings WHERE candidate_id = ?", (candidate_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_all_screenings_for_user(created_by: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT screenings.* FROM screenings
        JOIN jobs ON screenings.job_id = jobs.id
        WHERE jobs.created_by = ?
        """,
        (created_by,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_screenings_for_candidate(candidate_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM screenings WHERE candidate_id = ?", (candidate_id,))
    conn.commit()
    conn.close()