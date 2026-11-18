import os
import re
import email
from email import policy
import pymupdf
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

from app.config import settings
from app.ingestion.pdf_processor import PDFProcessor
from app.rag.chunker import NoticeChunker
from app.rag.vector_store import get_vector_store
from app.database.repository import NoticeRepository, DeadlineRepository, ConflictRepository
from app.intelligence.deadline_extractor import DeadlineExtractor
from app.intelligence.conflict_detector import ConflictDetector

router = APIRouter(prefix="/api/upload-pdf", tags=["PDF & Document Upload"])

@router.post("")
async def upload_document(request: Request) -> Dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    filename = "uploaded_document.pdf"
    file_bytes = b""

    if "multipart/form-data" in content_type:
        raw_body = await request.body()
        raw_headers = f"Content-Type: {content_type}\r\n\r\n".encode("utf-8")
        try:
            msg = email.message_from_bytes(raw_headers + raw_body, policy=policy.default)
            for part in msg.iter_parts():
                fn = part.get_filename()
                if fn:
                    filename = fn
                    file_bytes = part.get_payload(decode=True) or b""
                    break
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse multipart body: {str(e)}")
    else:
        file_bytes = await request.body()
        custom_fn = request.headers.get("x-filename")
        if custom_fn:
            filename = custom_fn

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="No file data received. Please select a valid PDF circular or image to upload."
        )

    lower_name = filename.lower()
    is_image = any(lower_name.endswith(ext) for ext in [".png", ".jpg", ".jpeg"])
    is_pdf = lower_name.endswith(".pdf") or file_bytes.startswith(b"%PDF")

    if not is_pdf and not is_image:
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only PDF circulars (.pdf) and notice images (.png, .jpg, .jpeg) are accepted."
        )

    # Sanitize filename
    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    notice_id = f"UPL-{abs(hash(safe_name + str(len(file_bytes)))) % 100000:05d}"
    
    # If image, convert to PDF via PyMuPDF
    if is_image:
        try:
            img_type = "png" if lower_name.endswith(".png") else "jpeg"
            img_doc = pymupdf.open(stream=file_bytes, filetype=img_type)
            pdf_bytes = img_doc.convert_to_pdf()
            img_doc.close()
            file_bytes = pdf_bytes
            safe_name = os.path.splitext(safe_name)[0] + ".pdf"
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Failed to process image circular: {str(e)}")

    target_path = os.path.join(settings.PDF_DIR, f"{notice_id}_{safe_name}")

    try:
        with open(target_path, "wb") as f:
            f.write(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    # 1. PyMuPDF text & page extraction
    try:
        pages = PDFProcessor.extract_text_and_pages(target_path)
    except Exception as e:
        if os.path.exists(target_path):
            os.remove(target_path)
        raise HTTPException(
            status_code=422,
            detail=f"Could not parse PDF content with PyMuPDF: {str(e)}. Please ensure the document is not password-protected."
        )

    if not pages or not any(p["text"].strip() for p in pages):
        if is_image:
            # For image without text layer, provide structured notice description
            doc_title = os.path.splitext(filename)[0].replace("_", " ").title()
            fallback_text = f"Official College Circular Image: {doc_title}\nUploaded Document Archive ({filename})."
            pages = [{"page_number": 1, "text": fallback_text}]
        else:
            raise HTTPException(
                status_code=422,
                detail="The uploaded PDF appears to be empty or contains only scanned images without selectable text."
            )

    full_text = "\n\n".join([p["text"] for p in pages])
    meta = PDFProcessor.extract_metadata_from_text(full_text)

    # Determine descriptive title
    first_meaningful_line = ""
    for line in full_text.splitlines():
        clean = line.strip()
        if len(clean) > 12 and not clean.startswith("Page"):
            first_meaningful_line = clean[:120]
            break

    doc_title = first_meaningful_line or filename.replace(".pdf", "").replace("_", " ").title()

    uploaded_section = request.headers.get("x-section") or "Student Uploads"
    uploaded_dept = request.headers.get("x-department")

    notice_record = {
        "id": notice_id,
        "ref_no": meta.get("ref_no") or notice_id,
        "title": doc_title,
        "issue_date": meta.get("date"),
        "category": meta.get("category", "Uploaded Circular"),
        "section": uploaded_section,
        "department": uploaded_dept,
        "content_type": "uploaded_pdf" if is_pdf else "uploaded_image",
        "summary": full_text[:350] + "..." if len(full_text) > 350 else full_text,
        "full_text": full_text,
        "pdf_path": target_path,
        "source_url": f"local://upload/{safe_name}",
        "source_institution": "User Upload",
        "status": "Active (User Upload)",
        "chunks_count": 0
    }

    # 2. Chunking with metadata
    chunker = NoticeChunker(chunk_size=700, chunk_overlap=120)
    chunks = chunker.split_notice_pages(notice_record, pages)

    # 3. Embedding and ChromaDB vectorization
    vector_store = get_vector_store()
    indexed_chunks = vector_store.add_chunks(chunks)
    notice_record["chunks_count"] = indexed_chunks

    # 4. Insert Notice record into SQLite
    NoticeRepository.insert_notice(notice_record)

    # 5. Extract deadlines and store in database
    extracted_deadlines = DeadlineExtractor.extract_deadlines_from_notice(notice_record)
    for dl in extracted_deadlines:
        DeadlineRepository.insert_deadline(dl)

    # 6. Detect potential date conflicts
    all_notices = NoticeRepository.get_all_notices()
    conflicts = ConflictDetector.detect_conflicts(all_notices)
    for conf in conflicts:
        ConflictRepository.insert_conflict(conf)

    return {
        "status": "success",
        "message": f"Successfully indexed '{filename}' ({len(pages)} pages, {indexed_chunks} vector chunks).",
        "notice_id": notice_id,
        "title": doc_title,
        "page_count": len(pages),
        "chunks_indexed": indexed_chunks,
        "deadlines_extracted": len(extracted_deadlines),
        "conflicts_detected": len(conflicts),
        "document": {
            "id": notice_id,
            "title": doc_title,
            "filename": filename,
            "category": notice_record["category"],
            "page_count": len(pages),
            "chunks_count": indexed_chunks,
            "source_institution": "User Upload"
        }
    }
