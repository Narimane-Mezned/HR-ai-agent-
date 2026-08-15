from app.db.database import db_connection


def init_call_logs_table() -> None:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                estimated_cost REAL,
                latency_ms INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def log_call(model: str, prompt_tokens: int, completion_tokens: int, estimated_cost: float, latency_ms: int) -> None:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO call_logs (model, prompt_tokens, completion_tokens, estimated_cost, latency_ms)
               VALUES (?, ?, ?, ?, ?)""",
            (model, prompt_tokens, completion_tokens, estimated_cost, latency_ms),
        )
        conn.commit()


def get_call_summary() -> dict:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_calls,
                SUM(prompt_tokens) as total_prompt_tokens,
                SUM(completion_tokens) as total_completion_tokens,
                SUM(estimated_cost) as total_cost,
                AVG(latency_ms) as avg_latency_ms
            FROM call_logs
        """)
        row = cursor.fetchone()
        return dict(row)