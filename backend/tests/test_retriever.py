import pytest
from app.rag.vector_store import get_vector_store

@pytest.fixture(autouse=True)
def setup_test_vectors():
    store = get_vector_store()
    test_chunks = [
        {
            "id": "test_chunk_fee_1",
            "text": "Notice regarding tuition fee submission. The last date to pay pending semester dues is March 31, 2026.",
            "metadata": {
                "notice_id": "TEST-FEE-01",
                "title": "Academic Tuition Fee Submission Schedule",
                "category": "Fees & Finance",
                "page": 1,
                "issue_date": "2026-03-01",
                "source_url": "https://college.edu/notices/fee-2026"
            }
        },
        {
            "id": "test_chunk_exam_1",
            "text": "Office of Controller of Examinations: 7th semester exam date postponed to May 20, 2026 due to administrative reasons.",
            "metadata": {
                "notice_id": "TEST-EXAM-02",
                "title": "Revised 7th Semester Examination Date",
                "category": "Examinations",
                "page": 1,
                "issue_date": "2026-04-10",
                "source_url": "https://college.edu/notices/exam-revised"
            }
        }
    ]
    store.add_chunks(test_chunks)

def test_semantic_retrieval_relevance():
    store = get_vector_store()
    assert store.count() > 0, "Vector store should contain indexed notices"
    
    # Query for fee submission
    fee_results = store.similarity_search("When is the last date to pay tuition fees?", top_k=2)
    assert len(fee_results) > 0
    top_meta = fee_results[0]["metadata"]
    assert "fee" in top_meta["title"].lower() or "dues" in fee_results[0]["text"].lower()

def test_semantic_retrieval_exam_date():
    store = get_vector_store()
    exam_results = store.similarity_search("7th semester exam date postponed", top_k=2)
    assert len(exam_results) > 0
    top_meta = exam_results[0]["metadata"]
    assert "exam" in top_meta["title"].lower() or "revised" in top_meta["title"].lower()
