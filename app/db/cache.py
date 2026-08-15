import hashlib
import json

from app.db.database import db_connection


def init_cache_table() -> None:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screening_cache (
                cache_key TEXT PRIMARY KEY,
                result_json TEXT NOT NULL,
                model_used TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def make_cache_key(cv_text: str, job_description: str, model: str) -> str:
    combined = f"{model}::{cv_text}::{job_description}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def get_cached_result(cache_key: str) -> dict | None:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT result_json FROM screening_cache WHERE cache_key = ?", (cache_key,))
        row = cursor.fetchone()

        if row:
            return json.loads(row["result_json"])
        return None


def save_cached_result(cache_key: str, result: dict, model: str) -> None:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO screening_cache (cache_key, result_json, model_used) VALUES (?, ?, ?)",
            (cache_key, json.dumps(result), model),
        )
        conn.commit()