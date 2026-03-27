import sqlite3

DB_NAME = "participants.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS participants (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        code TEXT
    )
    """)
    conn.commit()
    conn.close()

def add_participant(user_id: int, username: str, code: str) -> None:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO participants (user_id, username, code) VALUES (?, ?, ?)",
        (user_id, username, code)
    )
    conn.commit()
    conn.close()

def has_participated(user_id: int) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM participants WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None