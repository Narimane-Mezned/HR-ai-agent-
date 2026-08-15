import bcrypt
import sqlite3
from app.db.database import db_connection


class UsernameAlreadyExistsError(Exception):
    pass


def init_users_table() -> None:
    with db_connection() as conn:
        cursor = conn.cursor()
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
        conn.commit()


def create_user(username: str, password: str, company_name: str, email: str = "") -> int:
    normalized = username.strip().lower()
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, company_name, email) VALUES (?, ?, ?, ?)",
                (normalized, password_hash, company_name.strip(), email.strip()),
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise UsernameAlreadyExistsError(f"Username '{normalized}' is already taken.")

def verify_user(username: str, password: str) -> bool:
    normalized = username.strip().lower()
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (normalized,))
        row = cursor.fetchone()
        if not row:
            return False
        return bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8"))


def get_user_profile(username: str) -> dict | None:
    normalized = username.strip().lower()
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, company_name, email, created_at FROM users WHERE username = ?", (normalized,))
        row = cursor.fetchone()
        return dict(row) if row else None