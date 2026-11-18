import pytest
from app.rag.vector_store import get_vector_store
from app.rag.generator import CampusRAGGenerator
from app.intelligence.conflict_detector import ConflictDetector

@pytest.fixture(autouse=True)
def setup_rag_test_vectors():
    store = get_vector_store()
    test_chunks = [
        {
            "id": "rag_test_exam_01",
            "text": "Office of the Controller of Examinations: End semester theory exams commence from 25 May 2026. Hall tickets available on portal.",
            "metadata": {
                "notice_id": "COE-TEST-89",
                "title": "Revised End Semester Exam Schedule May 2026",
                "category": "Examinations",
                "page": 1,
                "issue_date": "2026-05-01",
                "source_url": "https://college.edu/notices/exam-may-2026"
            }
        }
    ]
    store.add_chunks(test_chunks)

def test_rag_answers_examination_query():
    store = get_vector_store()
    q = "What is the revised start date for end semester examinations?"
    chunks = store.similarity_search(q, top_k=3)
    
    assert len(chunks) > 0, "Should retrieve chunks from vector store"
    res = CampusRAGGenerator.generate_answer(q, chunks)
    
    assert res["grounded"] is True
    assert len(res["sources"]) > 0
    cited_ids = [s["id"] for s in res["sources"]]
    assert any("COE" in cid or "TEST" in cid or "89" in cid or "WEB" in cid or "GECA" in cid for cid in cited_ids)

def test_rag_anti_hallucination_on_unrelated_query():
    q = "How do I make chocolate cake?"
    # ChromaDB similarity search returns low scores for completely unrelated content
    res = CampusRAGGenerator.generate_answer(q, [])
    
    assert res["grounded"] is False
    assert "Official Notice Not Found" in res["answer"]
    assert len(res["sources"]) == 0

def test_conflict_detection_engine():
    # Pass two notices where one revises the other
    mock_notices = [
        {
            "id": "NOT-2026-089",
            "title": "Revised Schedule of End-Semester Examinations 2026",
            "category": "Examinations",
            "issue_date": "2026-05-02",
            "full_text": "This is a revised circular. End-semester exams postponed to May 25, 2026.",
            "supersedes": "NOT-2026-072"
        },
        {
            "id": "NOT-2026-072",
            "title": "Original Schedule of End-Semester Examinations 2026",
            "category": "Examinations",
            "issue_date": "2026-04-15",
            "full_text": "End-semester examinations will commence from May 10, 2026."
        }
    ]
    conflicts = ConflictDetector.detect_conflicts(mock_notices)
    
    assert len(conflicts) >= 1
    c = conflicts[0]
    assert "Revision" in c["topic"]
    assert c["superseding_notice_id"] == "NOT-2026-089"
    assert c["original_notice_id"] == "NOT-2026-072"
