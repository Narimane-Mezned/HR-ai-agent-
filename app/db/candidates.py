from app.db.database import get_connection


def create_candidate(name: str, cv_text: str, created_by: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO candidates (name, cv_text, created_by) VALUES (?, ?, ?)",
        (name, cv_text, created_by),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_candidate(candidate_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def list_candidates(created_by: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates WHERE created_by = ? ORDER BY created_at DESC", (created_by,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_candidate_cv(candidate_id: int, name: str, cv_text: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE candidates SET name = ?, cv_text = ? WHERE id = ?", (name, cv_text, candidate_id))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def delete_candidate(candidate_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted