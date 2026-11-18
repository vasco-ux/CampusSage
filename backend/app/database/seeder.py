import os
import json
from typing import Dict, Any
from app.database.repository import NoticeRepository, DeadlineRepository, ConflictRepository
from app.rag.chunker import NoticeChunker
from app.rag.vector_store import get_vector_store

SEED_FILE = os.path.join(os.path.dirname(__file__), "seed_data.json")

def seed_database_if_empty() -> Dict[str, Any]:
    """
    Auto-seeds the SQLite database and ChromaDB vector store on fresh cloud instances
    (such as Render Free Tier) from verified official college seed notices.
    """
    existing_count = NoticeRepository.count_notices()
    if existing_count > 0:
        return {"status": "skipped", "message": f"Database already contains {existing_count} notices."}

    if not os.path.exists(SEED_FILE):
        return {"status": "warning", "message": "No seed_data.json file found."}

    try:
        with open(SEED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        notices = data.get("notices", [])
        deadlines = data.get("deadlines", [])
        conflicts = data.get("conflicts", [])

        # 1. Insert notices
        for n in notices:
            NoticeRepository.insert_notice(n)

        # 2. Insert deadlines
        for dl in deadlines:
            DeadlineRepository.insert_deadline(dl)

        # 3. Insert conflicts
        for conf in conflicts:
            ConflictRepository.insert_conflict(conf)

        # 4. Vectorize notices into ChromaDB if vector store is empty
        try:
            vector_store = get_vector_store()
            if vector_store.count() == 0:
                chunker = NoticeChunker(chunk_size=700, chunk_overlap=120)
                total_chunks = 0
                for notice in notices:
                    text = notice.get("full_text") or notice.get("summary") or notice["title"]
                    pages = [{"page_number": 1, "text": text}]
                    chunks = chunker.split_notice_pages(notice, pages)
                    if chunks:
                        indexed = vector_store.add_chunks(chunks)
                        total_chunks += indexed
                print(f"[SEEDER] Successfully indexed {total_chunks} vector chunks into ChromaDB.")
        except Exception as vec_err:
            print(f"[SEEDER] Note: Vector store indexing deferred: {vec_err}")

        print(f"[SEEDER] Successfully seeded {len(notices)} notices, {len(deadlines)} deadlines, and {len(conflicts)} conflicts.")
        return {
            "status": "success",
            "notices": len(notices),
            "deadlines": len(deadlines),
            "conflicts": len(conflicts)
        }
    except Exception as e:
        print(f"[SEEDER] Error during database seeding: {e}")
        return {"status": "error", "error": str(e)}
