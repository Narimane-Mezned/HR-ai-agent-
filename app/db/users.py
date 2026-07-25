import bcrypt
from app.db.database import get_connection


def init_users_table() -> None:
    conn = get_connection()
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
    conn.close()


def create_user(username: str, password: str, company_name: str, email: str = "") -> int:
    normalized = username.strip().lower()
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password_hash, company_name, email) VALUES (?, ?, ?, ?)",
        (normalized, password_hash, company_name.strip(), email.strip()),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def verify_user(username: str, password: str) -> bool:
    normalized = username.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (normalized,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8"))


def get_user_profile(username: str) -> dict | None:
    normalized = username.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, company_name, email, created_at FROM users WHERE username = ?", (normalized,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None