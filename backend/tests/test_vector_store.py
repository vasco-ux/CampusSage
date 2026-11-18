import pytest
from app.rag.chunker import NoticeChunker
from app.rag.embeddings import campus_embedder

def test_chunker_metadata_preservation():
    notice = {
        "id": "NOT-TEST-1",
        "ref_no": "TEST/REF/01",
        "title": "Test Circular Title",
        "issue_date": "2026-11-01",
        "category": "Academics"
    }
    pages = [{"page_number": 1, "text": "This is page 1 content. " * 30}]
    
    chunker = NoticeChunker(chunk_size=200, chunk_overlap=30)
    chunks = chunker.split_notice_pages(notice, pages)
    
    assert len(chunks) > 1
    for c in chunks:
        assert c["metadata"]["notice_id"] == "NOT-TEST-1"
        assert c["metadata"]["ref_no"] == "TEST/REF/01"
        assert c["metadata"]["page"] == 1

def test_embeddings_generation():
    texts = ["Examination schedule for B.Tech semester 7", "Tuition fees deadline notice"]
    embeddings = campus_embedder.embed_documents(texts)
    
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    assert len(embeddings[1]) == 384
