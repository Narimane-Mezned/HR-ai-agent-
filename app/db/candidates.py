from app.db.database import get_connection


def create_candidate(name: str, cv_text: str) -> int:
    
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO candidates (name, cv_text) VALUES (?, ?)",
        (name, cv_text),
    )

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_candidate(candidate_id: int) -> dict | None:
    """Fetches one candidate by id. Returns None if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def list_candidates() -> list[dict]:
   
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM candidates ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]