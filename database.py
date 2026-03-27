import sqlite3

DB_NAME = "participants.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Таблица участников
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS participants (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        code INTEGER
    )
    """)
    conn.commit()
    conn.close()

def add_participant(user_id: int, username: str, code: int) -> None:
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

def get_next_code() -> int:
    """Возвращает следующий числовой код (1, 2, 3 ...)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(code) FROM participants")
    result = cursor.fetchone()
    conn.close()
    if result[0] is None:
        return 1
    return result[0] + 1
