import pytest
from starlette.testclient import TestClient
from app.main import app
from app.database.connection import init_db

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_pdf_upload_endpoint():
    client = TestClient(app)
    
    # Construct a valid minimal mock PDF binary
    minimal_pdf_bytes = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>/Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 68>>stream\n"
        b"BT /F1 12 Tf 72 712 Td (College Circular: End Semester Exams start May 25, 2026.) Tj ET\n"
        b"endstream\nendobj\nxref\n0 5\n0000000000 65535 f\n"
        b"0000000010 00000 n\n0000000060 00000 n\n0000000117 00000 n\n0000000222 00000 n\n"
        b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n342\n%%EOF"
    )

    boundary = "----WebKitFormBoundaryUploadTest"
    content_type = f"multipart/form-data; boundary={boundary}"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="EndSemExamCircular.pdf"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode("utf-8") + minimal_pdf_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    res = client.post("/api/upload-pdf", content=body, headers={"Content-Type": content_type})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["page_count"] == 1
    assert data["chunks_indexed"] >= 1
    assert "document" in data

def test_ingestion_warning_on_zero_docs():
    client = TestClient(app)
    res = client.post("/api/ingest/scrape", json={"url": "https://example.com/invalid-notice-board-999"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "warning"
    assert data["notices_found"] == 0
    assert data["chunks_indexed"] == 0
    assert len(data["logs"]) > 0
