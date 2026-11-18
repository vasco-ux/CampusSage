import pytest
import os
from app.ingestion.pdf_processor import PDFProcessor
from app.config import settings

def test_pdf_extraction_page_count():
    pdf_path = os.path.join(settings.PDF_DIR, "NOT-2026-089.pdf")
    assert os.path.exists(pdf_path), "Sample PDF NOT-2026-089.pdf must exist"
    
    pages = PDFProcessor.extract_text_and_pages(pdf_path)
    assert len(pages) >= 1
    assert "COE/EXAM/2026/89" in pages[0]["text"]
    assert "November 22, 2026" in pages[0]["text"]

def test_metadata_extraction_heuristic():
    text = """OFFICE OF CONTROLLER OF EXAMINATIONS
    Ref. No: COE/EXAM/2026/89  Date: October 28, 2026
    CIRCULAR: End semester examination schedule revised."""
    
    meta = PDFProcessor.extract_metadata_from_text(text)
    assert meta["ref_no"] == "COE/EXAM/2026/89"
    assert "October 28, 2026" in meta["date"]
    assert meta["category"] == "Examinations"
