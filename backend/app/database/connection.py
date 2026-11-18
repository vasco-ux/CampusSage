import sqlite3
import os
from contextlib import contextmanager
from app.config import settings

DB_FILE = os.path.join(settings.DATA_DIR, "campussage.db")

def get_db_connection():
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db():
    """Context manager for safe database transactions."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initializes tables for notices, deadlines, conflicts, and crawl history."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Official College Notices Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id TEXT PRIMARY KEY,
            ref_no TEXT,
            title TEXT NOT NULL,
            issue_date TEXT,
            category TEXT,
            summary TEXT,
            full_text TEXT,
            pdf_path TEXT,
            source_url TEXT,
            source_institution TEXT DEFAULT 'Government Engineering College, Ajmer',
            status TEXT DEFAULT 'Active',
            superseded_by TEXT,
            chunks_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Add safe migrations for notices table
        cursor.execute("PRAGMA table_info(notices);")
        columns = [row["name"] for row in cursor.fetchall()]
        if "source_institution" not in columns:
            cursor.execute("ALTER TABLE notices ADD COLUMN source_institution TEXT DEFAULT 'Government Engineering College, Ajmer';")
        if "section" not in columns:
            cursor.execute("ALTER TABLE notices ADD COLUMN section TEXT;")
        if "department" not in columns:
            cursor.execute("ALTER TABLE notices ADD COLUMN department TEXT;")
        if "content_type" not in columns:
            cursor.execute("ALTER TABLE notices ADD COLUMN content_type TEXT DEFAULT 'pdf';")

        # 2. Upcoming Academic Deadlines Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS deadlines (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            deadline_date TEXT NOT NULL,
            category TEXT,
            urgency TEXT DEFAULT 'upcoming',
            source_notice_id TEXT,
            source_title TEXT,
            source_url TEXT,
            pdf_path TEXT,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Check deadline columns
        cursor.execute("PRAGMA table_info(deadlines);")
        dl_cols = [row["name"] for row in cursor.fetchall()]
        if "source_url" not in dl_cols:
            cursor.execute("ALTER TABLE deadlines ADD COLUMN source_url TEXT;")
        if "pdf_path" not in dl_cols:
            cursor.execute("ALTER TABLE deadlines ADD COLUMN pdf_path TEXT;")
        if "section" not in dl_cols:
            cursor.execute("ALTER TABLE deadlines ADD COLUMN section TEXT;")
        if "department" not in dl_cols:
            cursor.execute("ALTER TABLE deadlines ADD COLUMN department TEXT;")

        # 3. Conflicting / Superseded Notices Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conflicts (
            id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            severity TEXT DEFAULT 'medium',
            original_notice_id TEXT,
            superseding_notice_id TEXT,
            original_date TEXT,
            revised_date TEXT,
            resolution TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Check conflict columns
        cursor.execute("PRAGMA table_info(conflicts);")
        conf_cols = [row["name"] for row in cursor.fetchall()]
        if "created_at" not in conf_cols:
            cursor.execute("ALTER TABLE conflicts ADD COLUMN created_at TIMESTAMP;")

        # 4. Ingestion / Scrape Audit Logs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingestion_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT,
            notices_discovered INTEGER,
            chunks_indexed INTEGER,
            status TEXT,
            log_messages TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

    print(f"[DATABASE] SQLite schema verified and ready at {DB_FILE}")
