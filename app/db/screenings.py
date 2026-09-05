import json
from app.db.database import db_connection


def save_screening(candidate_id: int, job_id: int, result: dict) -> int:
    with db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO screenings
                (candidate_id, job_id, score, verdict, justification, category, skills, years_experience,
                 education, languages, location, confidence_level, confidence_reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(candidate_id, job_id) DO UPDATE SET
                score = excluded.score,
                verdict = excluded.verdict,
                justification = excluded.justification,
                category = excluded.category,
                skills = excluded.skills,
                years_experience = excluded.years_experience,
                education = excluded.education,
                languages = excluded.languages,
                location = excluded.location,
                confidence_level = excluded.confidence_level,
                confidence_reasoning = excluded.confidence_reasoning,
                created_at = CURRENT_TIMESTAMP
            """,
            (
                candidate_id, job_id,
                result.get("score"), result.get("verdict"), result.get("justification"),
                result.get("category"), json.dumps(result.get("skills", [])), result.get("years_experience"),
                result.get("education"), json.dumps(result.get("languages", [])), result.get("location"),
                result.get("confidence_level"), result.get("confidence_reasoning"),
            ),
        )
        conn.commit()

        cursor.execute("SELECT id FROM screenings WHERE candidate_id = ? AND job_id = ?", (candidate_id, job_id))
        row_id = cursor.fetchone()["id"]
        return row_id


def list_screenings_for_job(job_id: int) -> list[dict]:
    with db_connection() as conn:
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
        return [dict(row) for row in rows]


def list_screenings_for_candidate(candidate_id: int) -> list[dict]:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM screenings WHERE candidate_id = ?", (candidate_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def list_all_screenings_for_user(created_by: str) -> list[dict]:
    with db_connection() as conn:
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
        return [dict(row) for row in rows]


def delete_screenings_for_candidate(candidate_id: int) -> None:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM screenings WHERE candidate_id = ?", (candidate_id,))
        conn.commit()