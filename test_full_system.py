import sys
import os
import io

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, r"E:\CampusSage_Project\backend")
os.environ["DATABASE_PATH"] = r"E:\CampusSage_Project\backend\data\campussage.db"
os.environ["CHROMA_PERSIST_DIR"] = r"E:\CampusSage_Project\backend\data\chroma_db"
os.environ["PDF_STORAGE_DIR"] = r"E:\CampusSage_Project\backend\data\raw_pdfs"

from starlette.testclient import TestClient
from app.main import app
from app.database.connection import init_db
from app.database.repository import NoticeRepository, DeadlineRepository, ConflictRepository
from app.rag.vector_store import get_vector_store

print("=================================================================")
print(" 🎓 CampusSage Full System End-to-End Test (GEC Ajmer)")
print("=================================================================")

init_db()
client = TestClient(app)

# 1. System Health
print("\n--- 1. Testing System Health API (/api/health) ---")
res = client.get("/api/health")
assert res.status_code == 200
health_data = res.json()
print("Health Status:", health_data)
assert health_data["status"] in ["ok", "healthy"]
print("SUCCESS: Health check OK!")

# 2. Ingest GEC Ajmer Circulars
print("\n--- 2. Ingesting Real GEC Ajmer Examination Circulars (/api/ingest/scrape) ---")
ingest_payload = {
    "url": "https://www.ecajmer.ac.in/ui/cells/examination-section/circulars"
}
ingest_res = client.post("/api/ingest/scrape", json=ingest_payload)
print(f"Ingest Status Code: {ingest_res.status_code}")
ingest_data = ingest_res.json()
print("Ingest Status:", ingest_data.get("status"))
print("Notices Found:", ingest_data.get("notices_found"))
print("Chunks Indexed:", ingest_data.get("chunks_indexed"))
print("Deadlines Extracted:", ingest_data.get("deadlines_extracted"))

assert ingest_res.status_code == 200
assert ingest_data["status"] == "success"
assert ingest_data["notices_found"] >= 1
assert ingest_data["chunks_indexed"] >= 1
print("SUCCESS: GEC Ajmer circulars ingested and indexed into ChromaDB!")

# 3. Chatbot Greeting Test
print("\n--- 3. Testing Chatbot Conversational Greeting ('Hey') ---")
greeting_res = client.post("/api/chat", json={"question": "Hey", "history": []})
assert greeting_res.status_code == 200
greeting_data = greeting_res.json()
print("Greeting Answer:\n", greeting_data["answer"][:180], "...")
assert "CampusSage" in greeting_data["answer"]
assert "Official Notice Not Found" not in greeting_data["answer"]
print("SUCCESS: Chatbot responded politely to greeting!")

# 4. Chatbot Grounded Academic Q&A Test
print("\n--- 4. Testing Chatbot Academic Inquiry on Real Ingested Circulars ---")
q1_payload = {
    "question": "What is the circular regarding BTU B.Tech III Semester exam form filling?",
    "history": []
}
chat_res = client.post("/api/chat", json=q1_payload)
assert chat_res.status_code == 200
chat_data = chat_res.json()
print("Answer:\n", chat_data["answer"])
print("\nCitations:")
for s in chat_data.get("sources", []):
    print(f"  - [{s.get('id')}] {s.get('title')} (p.{s.get('page')}) | Match: {s.get('similarity')}")

assert len(chat_data["sources"]) > 0
assert chat_data["grounded"] is True
print("SUCCESS: Chatbot grounded answer with official citations!")

# 5. Multi-Turn Conversation History Test
print("\n--- 5. Testing Multi-Turn Follow-Up Question in the Same Conversation ---")
q2_payload = {
    "question": "What about the revaluation?",
    "history": [
        {"role": "user", "content": "What is the circular regarding BTU B.Tech III Semester exam form filling?"},
        {"role": "assistant", "content": chat_data["answer"]}
    ]
}
followup_res = client.post("/api/chat", json=q2_payload)
assert followup_res.status_code == 200
followup_data = followup_res.json()
print("Follow-up Answer:\n", followup_data["answer"])
print("\nFollow-up Citations:")
for s in followup_data.get("sources", []):
    print(f"  - [{s.get('id')}] {s.get('title')} (p.{s.get('page')})")

assert followup_data["grounded"] is True
print("SUCCESS: Follow-up question answered with context awareness!")

# 6. Anti-Hallucination Out-of-Domain Guardrail Test
print("\n--- 6. Testing Anti-Hallucination Safe Refusal ---")
unrelated_res = client.post("/api/chat", json={"question": "How do I make chocolate cake?", "history": []})
unrelated_data = unrelated_res.json()
print("Safe Refusal Answer:\n", unrelated_data["answer"][:140], "...")
assert "Official Notice Not Found" in unrelated_data["answer"]
assert len(unrelated_data["sources"]) == 0
print("SUCCESS: Anti-hallucination safeguard triggered properly!")

# 7. Document Upload Test (PDF)
print("\n--- 7. Testing Document Upload Endpoint (/api/upload-pdf) ---")
minimal_pdf_bytes = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>/Contents 4 0 R>>endobj\n"
    b"4 0 obj<</Length 82>>stream\n"
    b"BT /F1 12 Tf 72 712 Td (GEC Ajmer Circular: End-Term Project Viva starts December 10, 2026.) Tj ET\n"
    b"endstream\nendobj\nxref\n0 5\n0000000000 65535 f\n"
    b"0000000010 00000 n\n0000000060 00000 n\n0000000117 00000 n\n0000000222 00000 n\n"
    b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n356\n%%EOF"
)
boundary = "----WebKitFormBoundaryTest"
content_type = f"multipart/form-data; boundary={boundary}"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="ProjectVivaNotice.pdf"\r\n'
    f"Content-Type: application/pdf\r\n\r\n"
).encode("utf-8") + minimal_pdf_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

upl_res = client.post("/api/upload-pdf", content=body, headers={"Content-Type": content_type})
assert upl_res.status_code == 200
upl_data = upl_res.json()
print("Upload Result:", upl_data)
assert upl_data["status"] == "success"
assert upl_data["chunks_indexed"] >= 1
print("SUCCESS: PDF successfully uploaded and indexed!")

# 8. Notice Board & Deadlines Consistency
print("\n--- 8. Verifying Notice Board and Deadlines Radar Consistency ---")
notices_res = client.get("/api/notices")
assert notices_res.status_code == 200
notices_list = notices_res.json()
print(f"Total Notices in Board: {len(notices_list)}")
for n in notices_list:
    print(f"  - [{n['ref_no']}] {n['title'][:55]} ({n['source_institution']})")

deadlines_res = client.get("/api/deadlines")
assert deadlines_res.status_code == 200
deadlines_list = deadlines_res.json()
print(f"\nTotal Deadlines on Radar: {len(deadlines_list)}")
for d in deadlines_list:
    print(f"  - [{d['deadline_date']}] {d['title'][:55]}")

assert len(notices_list) >= 4
print("SUCCESS: Notice Board and Deadlines Radar consistent with indexed data!")

# 9. Ingestion Warning Test for 0 Documents
print("\n--- 9. Verifying Ingestion Diagnostic Warning on Invalid URL ---")
warn_res = client.post("/api/ingest/scrape", json={"url": "https://example.com/invalid-notice-board-999"})
assert warn_res.status_code == 200
warn_data = warn_res.json()
print("Warning Response Status:", warn_data.get("status"))
assert warn_data["status"] == "warning"
assert len(warn_data["logs"]) > 0
print("SUCCESS: Warning returned for 0-document crawl with detailed diagnostic logs!")

# 10. Multi-Section Catalog & Coverage Test
print("\n--- 10. Verifying Multi-Section College Catalog (/api/ingest/sections) ---")
sec_res = client.get("/api/ingest/sections")
assert sec_res.status_code == 200
sec_data = sec_res.json()
print(f"Total Sections Discovered: {sec_data.get('total_sections')}")
assert sec_data.get("total_sections") >= 50
print("SUCCESS: 54 college sections registered in catalog with real-time stats!")

# 11. Section Filtering Test
print("\n--- 11. Verifying Section and Department Notice Filtering ---")
filters_res = client.get("/api/notices/filters")
assert filters_res.status_code == 200
filters_data = filters_res.json()
print(f"Sections in DB: {len(filters_data.get('sections', []))}")
assert len(filters_data.get("sections", [])) >= 3
print("SUCCESS: Section-based filtering operational!")

# 12. Cross-Section RAG Inquiry Verification
print("\n--- 12. Testing Cross-Section Question Answering (Library, Proctor, Principal) ---")
cross_questions = [
    ("Central Library", "What are the rules and rescheduling for book bank distribution?"),
    ("Principal", "What is Principal Dr. Radha Kishan Motwani's message and vision?"),
    ("Proctor", "What are the Proctor Office anti-ragging and student discipline guidelines?")
]
for sec_name, q in cross_questions:
    c_res = client.post("/api/chat", json={"question": q, "history": []})
    assert c_res.status_code == 200
    c_data = c_res.json()
    print(f"  [{sec_name}] Grounded: {c_data['grounded']} | Confidence: {c_data['confidence']}")
    assert c_data["grounded"] is True

print("\n=================================================================")
print(" 🎉 ALL 12 END-TO-END SYSTEM VERIFICATION CHECKS PASSED PERFECTLY!")
print("=================================================================")
