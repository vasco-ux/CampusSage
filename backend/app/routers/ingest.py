from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Dict, Any, List, Optional

from app.routers.schemas import IngestRequest
from app.ingestion.scraper import NoticeScraper
from app.ingestion.sections_catalog import ALL_SECTIONS, SECTIONS_BY_SLUG, get_section_by_slug
from app.database.repository import NoticeRepository, DeadlineRepository, ConflictRepository
from app.rag.chunker import NoticeChunker
from app.rag.vector_store import get_vector_store
from app.ingestion.pdf_processor import PDFProcessor
from app.intelligence.deadline_extractor import DeadlineExtractor
from app.intelligence.conflict_detector import ConflictDetector

router = APIRouter(prefix="/api/ingest", tags=["Website Ingestion Hub"])

def _index_scraped_notices(notices: List[Dict[str, Any]], logs: List[str], target_label: str) -> Dict[str, Any]:
    """
    Standard pipeline: chunks, embeds into ChromaDB, saves to SQLite,
    extracts academic deadlines, and detects schedule conflicts.
    """
    if not notices:
        return {
            "status": "warning",
            "message": f"Zero notices or documents discovered from '{target_label}'.",
            "target": target_label,
            "notices_found": 0,
            "pdfs_downloaded": 0,
            "chunks_indexed": 0,
            "deadlines_extracted": 0,
            "logs": logs
        }

    vector_store = get_vector_store()
    chunker = NoticeChunker(chunk_size=700, chunk_overlap=120)
    total_chunks = 0
    all_deadlines_found = 0

    for notice in notices:
        # 1. Extract pages and chunk
        pages = notice.get("_pages") or []
        if not pages and notice.get("pdf_path"):
            try:
                pages = PDFProcessor.extract_text_and_pages(notice["pdf_path"])
            except Exception:
                pass
        if not pages:
            pages = [{"page_number": 1, "text": notice["full_text"]}]

        chunks = chunker.split_notice_pages(notice, pages)
        indexed_count = vector_store.add_chunks(chunks)
        total_chunks += indexed_count
        notice["chunks_count"] = indexed_count

        # 2. Insert into SQLite
        NoticeRepository.insert_notice(notice)

        # 3. Extract and store academic deadlines
        extracted_dls = DeadlineExtractor.extract_deadlines_from_notice(notice)
        for dl in extracted_dls:
            DeadlineRepository.insert_deadline(dl)
            all_deadlines_found += 1

    # 4. Check for conflicts across all notices
    all_notices = NoticeRepository.get_all_notices()
    detected_conflicts = ConflictDetector.detect_conflicts(all_notices)
    for conf in detected_conflicts:
        ConflictRepository.insert_conflict(conf)

    return {
        "status": "success",
        "message": f"Successfully ingested {len(notices)} official items ({total_chunks} vector chunks) from '{target_label}'.",
        "target": target_label,
        "notices_found": len(notices),
        "pdfs_downloaded": len([n for n in notices if n.get("pdf_path")]),
        "chunks_indexed": total_chunks,
        "deadlines_extracted": all_deadlines_found,
        "logs": logs
    }

@router.get("/sections")
def get_college_sections():
    """
    Returns the comprehensive catalog of official GEC Ajmer sections (Cells, Departments, Administration)
    along with real-time indexing statistics for each.
    """
    # Fetch live stats from SQLite
    stats = NoticeRepository.get_section_stats()
    stats_by_name = {s["section_name"].lower(): s for s in stats}

    catalog = []
    for sec in ALL_SECTIONS:
        name = sec["name"]
        matched_stat = (
            stats_by_name.get(name.lower()) or
            stats_by_name.get(sec["slug"].lower()) or
            {}
        )

        catalog.append({
            "slug": sec["slug"],
            "name": name,
            "category": sec.get("category", "General"),
            "type": sec.get("type", "cell"),
            "public_url": sec.get("public_url"),
            "description": sec.get("description", ""),
            "doc_count": matched_stat.get("doc_count", 0),
            "chunks_count": matched_stat.get("total_chunks", 0),
            "last_indexed": matched_stat.get("last_indexed")
        })

    return {
        "total_sections": len(catalog),
        "institution": "Government Engineering College, Ajmer",
        "sections": catalog
    }

@router.post("/section/{slug}")
def ingest_specific_section(slug: str, max_items: int = Query(5, description="Max circulars to ingest")):
    """
    Crawls and indexes a specific official college section (e.g. 'proctor', 'hostels', 'cs-it', 'examination-section').
    """
    section = get_section_by_slug(slug)
    if not section:
        raise HTTPException(status_code=404, detail=f"College section '{slug}' not found in official catalog.")

    scraper = NoticeScraper()
    notices = scraper.scrape_section(section, max_items=max_items)
    return _index_scraped_notices(notices, scraper.logs, section["name"])

@router.post("/scrape-all")
def ingest_all_sections(
    category: Optional[str] = Query(None, description="Optional category filter (e.g. 'Engineering Departments')"),
    max_per_section: int = Query(3, description="Max items per section")
):
    """
    Crawls and indexes either all college sections or all sections within a category.
    """
    scraper = NoticeScraper()
    target_sections = ALL_SECTIONS
    if category and category != "All":
        target_sections = [s for s in ALL_SECTIONS if s.get("category") == category]

    notices = scraper.scrape_all_sections(sections=target_sections, max_per_section=max_per_section)
    label = f"College-Wide Crawl ({len(target_sections)} sections)"
    return _index_scraped_notices(notices, scraper.logs, label)

@router.post("")
@router.post("/scrape")
def trigger_scrape(req: IngestRequest):
    """
    General scrape endpoint. Supports section slug or custom URL.
    """
    scraper = NoticeScraper()

    if req.section_slug:
        sec = get_section_by_slug(req.section_slug)
        if not sec:
            raise HTTPException(status_code=404, detail=f"Section '{req.section_slug}' not found.")
        notices = scraper.scrape_section(sec, max_items=req.max_items or 5)
        return _index_scraped_notices(notices, scraper.logs, sec["name"])

    target_url = req.url or "https://www.ecajmer.ac.in/"
    notices = scraper.scrape_notices_from_url(target_url, max_items=req.max_items or 6)
    return _index_scraped_notices(notices, scraper.logs, target_url)

@router.post("/clear-data")
def clear_all_data():
    """Removes all notices, deadlines, conflicts, and ChromaDB vectors for a clean state."""
    from app.database.connection import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notices;")
        cursor.execute("DELETE FROM deadlines;")
        cursor.execute("DELETE FROM conflicts;")
        cursor.execute("DELETE FROM ingestion_logs;")
        conn.commit()

    store = get_vector_store()
    store.reset()

    return {
        "status": "success",
        "message": "Knowledge base and ChromaDB vector store cleared successfully."
    }
