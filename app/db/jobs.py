from app.db.database import db_connection


def create_job(title: str, description: str, requirements: str, created_by: str) -> int:
    with db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO jobs (title, description, requirements, created_by) VALUES (?, ?, ?, ?)",
            (title, description, requirements, created_by.strip()),
        )

        conn.commit()
        return cursor.lastrowid


def get_job(job_id: int) -> dict | None:
    with db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()

        return dict(row) if row else None


def list_jobs(created_by: str = None) -> list[dict]:
    with db_connection() as conn:
        cursor = conn.cursor()

        if created_by:
            cursor.execute("SELECT * FROM jobs WHERE created_by = ? ORDER BY created_at DESC", (created_by,))
        else:
            cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")

        rows = cursor.fetchall()

        return [dict(row) for row in rows]


def update_job(job_id: int, title: str = None, description: str = None, requirements: str = None) -> bool:
    existing = get_job(job_id)
    if not existing:
        return False

    updated_title = title if title is not None else existing["title"]
    updated_description = description if description is not None else existing["description"]
    updated_requirements = requirements if requirements is not None else existing["requirements"]

    with db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE jobs SET title = ?, description = ?, requirements = ? WHERE id = ?",
            (updated_title, updated_description, updated_requirements, job_id),
        )

        conn.commit()
        return True


def delete_job(job_id: int) -> bool:
    with db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        conn.commit()

        return cursor.rowcount > 0