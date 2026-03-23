import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/maintainiq.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_name TEXT NOT NULL,
            last_service_date TEXT,
            risk_score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'OK',
            predicted_failure TEXT,
            recommended_action TEXT,
            spare_parts TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_name TEXT,
            log_date TEXT,
            log_text TEXT,
            source_file TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("Database initialized.")