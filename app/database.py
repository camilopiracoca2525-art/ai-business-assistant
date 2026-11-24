import sqlite3
from contextlib import contextmanager
from app.config import DATABASE_PATH

@contextmanager
def connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def initialize():
    with connection() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(conversation_id) REFERENCES conversations(id)
        )""")

def create_conversation() -> int:
    with connection() as db:
        cur = db.execute("INSERT INTO conversations DEFAULT VALUES")
        return int(cur.lastrowid)

def add_message(cid: int, role: str, content: str):
    with connection() as db:
        db.execute(
            "INSERT INTO messages(conversation_id, role, content) VALUES (?, ?, ?)",
            (cid, role, content),
        )

def get_history(cid: int, limit: int):
    with connection() as db:
        rows = db.execute(
            "SELECT role, content FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT ?",
            (cid, limit),
        ).fetchall()
    return [dict(row) for row in reversed(rows)]

def counts():
    with connection() as db:
        return {
            "conversations": db.execute("SELECT COUNT(*) FROM conversations").fetchone()[0],
            "stored_messages": db.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
        }
