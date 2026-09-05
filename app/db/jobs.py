from app.db.database import db_connection


def create_job(
    title: str, description: str, requirements: str, created_by: str,
    location: str = None, remote_policy: str = None, experience_level: str = None,
) -> int:
    with db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO jobs
               (title, description, requirements, created_by, location, remote_policy, experience_level)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, description, requirements, created_by.strip(), location, remote_policy, experience_level),
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


def update_job(
    job_id: int, title: str = None, description: str = None, requirements: str = None,
    location: str = None, remote_policy: str = None, experience_level: str = None,
) -> bool:
    existing = get_job(job_id)
    if not existing:
        return False

    updated_title = title if title is not None else existing["title"]
    updated_description = description if description is not None else existing["description"]
    updated_requirements = requirements if requirements is not None else existing["requirements"]
    updated_location = location if location is not None else existing["location"]
    updated_remote_policy = remote_policy if remote_policy is not None else existing["remote_policy"]
    updated_experience_level = experience_level if experience_level is not None else existing["experience_level"]

    with db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """UPDATE jobs SET title = ?, description = ?, requirements = ?,
               location = ?, remote_policy = ?, experience_level = ? WHERE id = ?""",
            (
                updated_title, updated_description, updated_requirements,
                updated_location, updated_remote_policy, updated_experience_level, job_id,
            ),
        )

        conn.commit()
        return True


def delete_job(job_id: int) -> bool:
    with db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        conn.commit()

        return cursor.rowcount > 0