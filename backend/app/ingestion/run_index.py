import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.ingestion.indexer import index_all_notices_to_chromadb
from app.rag.vector_store import get_vector_store

if __name__ == "__main__":
    indexed = index_all_notices_to_chromadb()
    store = get_vector_store()
    print("Total in ChromaDB collection:", store.count())

    results = store.similarity_search("What is the deadline for tuition fees?", top_k=2)
    print("\n--- Semantic Search Test Results ---")
    for r in results:
        meta = r["metadata"]
        ref = meta.get("ref_no")
        title = meta.get("title")
        score = r["score"]
        print(f"Match: {ref} - {title} (Similarity: {score})")
        print("Snippet:", repr(r["text"][:95]))
