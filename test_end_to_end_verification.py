import sys
import os
import io

sys.path.insert(0, r"E:\CampusSage_Project\backend")
os.environ["DATABASE_PATH"] = r"E:\CampusSage_Project\backend\data\campussage.db"
os.environ["CHROMA_PERSIST_DIR"] = r"E:\CampusSage_Project\backend\data\chroma_db"
os.environ["PDF_STORAGE_DIR"] = r"E:\CampusSage_Project\backend\data\pdfs"

from starlette.testclient import TestClient
from app.main import app
from app.database.connection import init_db
from app.database.repository import NoticeRepository, DeadlineRepository, ConflictRepository
from app.rag.vector_store import get_vector_store

print("--- 1. Initializing DB and Vector Store ---")
init_db()
client = TestClient(app)

print("\n--- 2. Testing PDF Upload Endpoint (/api/upload-pdf) ---")
test_pdf_path = r"E:\CUET (UG) - 2026.pdf"
with open(test_pdf_path, "rb") as f:
    pdf_bytes = f.read()

# Using multipart/form-data upload
boundary = "----WebKitFormBoundaryCampusSageTest"
content_type = f"multipart/form-data; boundary={boundary}"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="CUET_UG_2026.pdf"\r\n'
    f"Content-Type: application/pdf\r\n\r\n"
).encode("utf-8") + pdf_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

response = client.post(
    "/api/upload-pdf",
    content=body,
    headers={"Content-Type": content_type}
)

print(f"Upload Status Code: {response.status_code}")
upload_data = response.json()
print("Upload Response:", upload_data)

assert response.status_code == 200, f"Upload failed: {response.text}"
assert upload_data["status"] == "success"
assert upload_data["page_count"] > 0
assert upload_data["chunks_indexed"] > 0
print(f"SUCCESS: Uploaded and indexed {upload_data['page_count']} pages, {upload_data['chunks_indexed']} chunks!")

print("\n--- 3. Testing RAG Chatbot Question-Answering Grounded in Uploaded PDF ---")
query_payload = {
    "question": "What is National Testing Agency announcing regarding CUET UG?",
    "history": []
}

chat_res = client.post("/api/chat", json=query_payload)
print(f"Chat Status Code: {chat_res.status_code}")
chat_data = chat_res.json()
print("\nAssistant Answer:")
print(chat_data.get("answer"))
print("\nSources Cited:")
for s in chat_data.get("sources", []):
    print(f"  - [{s.get('id')}] {s.get('title')} (Page {s.get('page')}) | Confidence: {s.get('similarity')}")

assert chat_res.status_code == 200
assert len(chat_data["sources"]) > 0, "No sources cited!"
assert "CUET" in chat_data["answer"] or "Common University" in chat_data["answer"] or "National Testing" in chat_data["answer"] or "testing" in chat_data["answer"].lower()
print("\nSUCCESS: Chatbot successfully grounded answer in uploaded document with citations!")

print("\n--- 4. Testing Ingestion Hub Diagnostic Warning for 0-Document Crawl ---")
ingest_res = client.post("/api/ingest", json={"url": "https://example.com/non-existent-notices"})
print(f"Ingest Status Code: {ingest_res.status_code}")
ingest_data = ingest_res.json()
print("Ingest Result Status:", ingest_data.get("status"))
print("Ingest Message:", ingest_data.get("message"))
print("Diagnostic Logs Sample:")
for log in ingest_data.get("logs", [])[:4]:
    print("  *", log)

assert ingest_data["status"] == "warning", f"Expected 'warning' status, got {ingest_data['status']}"
assert ingest_data["notices_found"] == 0
assert ingest_data["chunks_indexed"] == 0
print("\nSUCCESS: Ingestion returned WARNING status when 0 documents were found, with diagnostic logs!")

print("\nALL SYSTEM VERIFICATIONS PASSED PERFECTLY!")
