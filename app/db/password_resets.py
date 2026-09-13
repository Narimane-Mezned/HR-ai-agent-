import secrets
from datetime import datetime, timedelta
from app.db.database import db_connection

RESET_TOKEN_EXPIRE_HOURS = 24


def create_reset_token(username: str) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS)).isoformat()

    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO password_reset_tokens (username, token, expires_at) VALUES (?, ?, ?)",
            (username, token, expires_at),
        )
        conn.commit()

    return token


def get_username_for_valid_token(token: str) -> str | None:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, expires_at, used FROM password_reset_tokens WHERE token = ?",
            (token,),
        )
        row = cursor.fetchone()

    if not row:
        return None
    if row["used"]:
        return None
    if datetime.fromisoformat(row["expires_at"]) < datetime.utcnow():
        return None
    return row["username"]


def mark_token_used(token: str) -> None:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE password_reset_tokens SET used = 1 WHERE token = ?", (token,))
        conn.commit()