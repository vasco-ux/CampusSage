import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.database.connection import get_db
from app.rag.vector_store import get_vector_store
from app.ingestion.indexer import index_all_notices_to_chromadb

def clean_fake_sample_notices():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notices WHERE id LIKE 'NOT-2026-%';")
        cursor.execute("DELETE FROM deadlines WHERE id LIKE 'DL-%' AND source_notice_id LIKE 'NOT-2026-%';")
        cursor.execute("DELETE FROM conflicts WHERE id LIKE 'CONF-%' AND original_notice_id LIKE 'NOT-2026-%';")
        conn.commit()

    store = get_vector_store()
    store.reset()
    indexed = index_all_notices_to_chromadb()
    print(f"Cleaned fake sample notices! Remaining genuine indexed chunks: {indexed}")

if __name__ == "__main__":
    clean_fake_sample_notices()
