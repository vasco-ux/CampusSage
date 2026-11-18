from typing import List, Dict, Any
from app.database.repository import NoticeRepository
from app.ingestion.pdf_processor import PDFProcessor
from app.rag.chunker import NoticeChunker
from app.rag.vector_store import get_vector_store

def index_all_notices_to_chromadb() -> int:
    """
    Reads all notices from SQLite database.
    If a PDF exists, extracts text page-by-page via PyMuPDF.
    Splits into chunks with NoticeChunker.
    Embeds with Sentence-Transformers and stores in ChromaDB.
    """
    notices = NoticeRepository.get_all_notices()
    chunker = NoticeChunker(chunk_size=700, chunk_overlap=120)
    vector_store = get_vector_store()
    
    total_indexed_chunks = 0
    print(f"[INDEXER] Starting vector indexing for {len(notices)} notices...")

    for notice in notices:
        pdf_path = notice.get("pdf_path")
        pages = []

        if pdf_path:
            try:
                pages = PDFProcessor.extract_text_and_pages(pdf_path)
            except Exception as e:
                print(f"[INDEXER] Warning: Could not parse PDF {pdf_path}: {e}")

        # Fallback to full_text if PDF was not available or had no text
        if not pages:
            pages = [{"page_number": 1, "text": notice.get("full_text") or notice.get("summary") or notice["title"]}]

        chunks = chunker.split_notice_pages(notice, pages)
        indexed = vector_store.add_chunks(chunks)
        total_indexed_chunks += indexed

    print(f"[INDEXER] Indexing complete! Total chunks stored in ChromaDB: {total_indexed_chunks}")
    return total_indexed_chunks

if __name__ == "__main__":
    index_all_notices_to_chromadb()
