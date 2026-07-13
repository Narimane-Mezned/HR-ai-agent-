from app.db.database import get_connection


def save_screening(candidate_id: int, job_id: int, result: dict) -> int:
    
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO screenings (candidate_id, job_id, score, verdict, justification, category)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            candidate_id,
            job_id,
            result.get("score"),
            result.get("verdict"),
            result.get("justification"),
            result.get("category"),
        ),
    )

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


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