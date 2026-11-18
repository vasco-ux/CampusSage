import sys
import os

sys.path.insert(0, r"E:\CampusSage_Project\backend")
from app.database.connection import get_db, init_db
from app.rag.vector_store import get_vector_store

init_db()

with get_db() as conn:
    c = conn.cursor()
    c.execute("DELETE FROM notices;")
    deleted_notices = c.rowcount
    c.execute("DELETE FROM deadlines;")
    c.execute("DELETE FROM conflicts;")
    c.execute("DELETE FROM ingestion_logs;")
    print(f"Purged {deleted_notices} notices, deadlines, and conflicts from SQLite.")

store = get_vector_store()
store.reset()
print(f"ChromaDB reset to clean state. Total chunks: {store.count()}")
