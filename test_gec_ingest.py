import sys
import os

sys.path.insert(0, r"E:\CampusSage_Project\backend")
from app.database.connection import init_db
from app.ingestion.scraper import NoticeScraper
from app.rag.chunker import NoticeChunker
from app.rag.vector_store import get_vector_store
from app.database.repository import NoticeRepository, DeadlineRepository, ConflictRepository
from app.intelligence.deadline_extractor import DeadlineExtractor
from app.intelligence.conflict_detector import ConflictDetector

init_db()

print("\n--- Testing GEC Ajmer Ingestion for Examination Section ---")
url = "https://www.ecajmer.ac.in/ui/cells/examination-section/circulars"
scraper = NoticeScraper()
notices = scraper.scrape_notices_from_url(url, max_items=4)

print(f"\nScraped {len(notices)} notices.")
assert len(notices) > 0, "No notices scraped from GEC Ajmer!"

vector_store = get_vector_store()
chunker = NoticeChunker(chunk_size=700, chunk_overlap=120)
total_chunks = 0
total_dls = 0

for notice in notices:
    pages = notice.get("_pages") or []
    chunks = chunker.split_notice_pages(notice, pages)
    indexed_count = vector_store.add_chunks(chunks)
    total_chunks += indexed_count
    notice["chunks_count"] = indexed_count
    NoticeRepository.insert_notice(notice)
    
    deadlines = DeadlineExtractor.extract_deadlines_from_notice(notice)
    for dl in deadlines:
        DeadlineRepository.insert_deadline(dl)
        total_dls += 1

all_notices = NoticeRepository.get_all_notices()
conflicts = ConflictDetector.detect_conflicts(all_notices)
for conf in conflicts:
    ConflictRepository.insert_conflict(conf)

print(f"\nSUCCESSFULLY INDEXED:")
print(f"Total notices in DB: {len(all_notices)}")
print(f"Total chunks in ChromaDB: {vector_store.count()}")
print(f"Total deadlines extracted: {total_dls}")
print(f"Total conflicts detected: {len(conflicts)}")
