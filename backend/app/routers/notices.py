from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse
from typing import List, Optional, Dict, Any
import os
from app.database.repository import NoticeRepository

router = APIRouter(prefix="/api/notices", tags=["Notices"])

@router.get("", response_model=List[Dict[str, Any]])
def list_notices(
    category: Optional[str] = Query(None, description="Filter by category (Examinations, Fees, etc.)"),
    search: Optional[str] = Query(None, description="Search keyword in title or summary"),
    source: Optional[str] = Query(None, description="Filter by source institution or uploads"),
    section: Optional[str] = Query(None, description="Filter by college section"),
    department: Optional[str] = Query(None, description="Filter by department")
):
    """Retrieve all ingested official college notices with section and department filters."""
    cat_val = category if isinstance(category, str) else None
    search_val = search if isinstance(search, str) else None
    source_val = source if isinstance(source, str) else None
    sec_val = section if isinstance(section, str) else None
    dept_val = department if isinstance(department, str) else None

    return NoticeRepository.get_all_notices(
        category=cat_val,
        search=search_val,
        source=source_val,
        section=sec_val,
        department=dept_val
    )

@router.get("/filters")
def get_notice_filters():
    """Retrieve all available section, department, and category filter values."""
    return {
        "sections": NoticeRepository.get_distinct_sections(),
        "departments": NoticeRepository.get_distinct_departments(),
        "stats": NoticeRepository.get_section_stats()
    }

@router.get("/{notice_id}", response_model=Dict[str, Any])
def get_notice(notice_id: str):
    """Get single notice details by ID."""
    notice = NoticeRepository.get_notice_by_id(notice_id)
    if not notice:
        raise HTTPException(status_code=404, detail=f"Notice '{notice_id}' not found")
    return notice

@router.get("/pdf/{notice_id}")
def download_notice_pdf(notice_id: str):
    """Serve the original downloaded PDF circular if available or redirect to original source URL."""
    notice = NoticeRepository.get_notice_by_id(notice_id)
    if not notice:
        raise HTTPException(status_code=404, detail=f"Notice '{notice_id}' not found")
    
    if notice.get("content_type") == "webpage":
        raise HTTPException(status_code=404, detail="This item is an informational webpage overview, not a PDF circular.")

    pdf_path = notice.get("pdf_path")
    if pdf_path and os.path.exists(pdf_path):
        filename = os.path.basename(pdf_path)
        return FileResponse(pdf_path, media_type="application/pdf", filename=filename)
    
    # If local file not cached on disk, redirect to original source URL if available
    source_url = notice.get("source_url")
    if source_url and source_url.startswith("http") and (source_url.lower().endswith(".pdf") or "uploads/circulars" in source_url):
        return RedirectResponse(url=source_url)

    raise HTTPException(status_code=404, detail="PDF attachment not found for this notice")
