import sqlite3
import os
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "hr_agent.db")
DB_PATH = os.path.abspath(DB_PATH)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_connection():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                requirements TEXT,
                created_by TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                cv_text TEXT NOT NULL,
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screenings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL,
                score REAL,
                verdict TEXT,
                justification TEXT,
                category TEXT,
                skills TEXT,
                years_experience REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates(id),
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                company_name TEXT,
                email TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

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


        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_screenings_candidate_job
            ON screenings(candidate_id, job_id)
        """)



        def ensure_column(table, column, coltype):
            cursor.execute(f"PRAGMA table_info({table})")
            cols = [row[1] for row in cursor.fetchall()]
            if column not in cols:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
                logger.info("Migrated table '%s': added column '%s'", table, column)

        ensure_column("candidates", "created_by", "TEXT")
        ensure_column("candidates", "applied_job_id", "INTEGER")
        ensure_column("users", "company_name", "TEXT")
        ensure_column("users", "email", "TEXT")
        ensure_column("screenings", "skills", "TEXT")
        ensure_column("screenings", "years_experience", "REAL")
        ensure_column("candidates", "prescreening_answers", "TEXT")
        ensure_column("candidates", "email", "TEXT")
        ensure_column("candidates", "phone", "TEXT")
        ensure_column("candidates", "linkedin_url", "TEXT")
        ensure_column("candidates", "github_url", "TEXT")
        ensure_column("candidates", "status", "TEXT")
        ensure_column("candidates", "onboarding_checklist", "TEXT")
        ensure_column("candidates", "hired_for_job_id", "INTEGER")
        ensure_column("screenings", "education", "TEXT")
        ensure_column("screenings", "languages", "TEXT")
        ensure_column("screenings", "location", "TEXT")
        ensure_column("screenings", "confidence_level", "TEXT")
        ensure_column("screenings", "confidence_reasoning", "TEXT")
        ensure_column("jobs", "location", "TEXT")
        ensure_column("jobs", "remote_policy", "TEXT")
        ensure_column("jobs", "experience_level", "TEXT")
        ensure_column("candidates", "prescreening_flags", "TEXT")
        ensure_column("interviews", "reminder_sent", "INTEGER DEFAULT 0")
        ensure_column("candidates", "mentor_name", "TEXT")
        ensure_column("screenings", "decision", "TEXT")

        conn.commit()
        logger.info("Database initialized at %s", DB_PATH)


if __name__ == "__main__":
    init_db()