import os
from typing import List, Dict, Any, Optional
from app.config import settings
from app.rag.embeddings import campus_embedder

class CampusVectorStore:
    """Manages persistent ChromaDB vector storage for college notice chunks."""

    def __init__(self, persist_dir: Optional[str] = None, collection_name: Optional[str] = None):
        self.persist_dir = persist_dir or settings.CHROMA_DIR
        self.collection_name = collection_name or settings.CHROMA_COLLECTION
        self._client = None
        self._collection = None

    def _init_db(self):
        if self._collection is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            os.makedirs(self.persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            # Use cosine space for normalized semantic similarity
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine", "description": "Official college circular passages and metadata"}
            )

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """Embeds and indexes a list of chunk dictionaries into ChromaDB."""
        if not chunks:
            return 0
        self._init_db()

        ids = [c["id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        # Generate vectors via CampusEmbeddingManager
        embeddings = campus_embedder.embed_documents(texts)

        # Upsert into ChromaDB
        self._collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        return len(chunks)

    def similarity_search(
        self,
        query: str,
        top_k: int = 4,
        category: Optional[str] = None,
        section: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic similarity search for student queries against notice chunks.
        Supports optional category and section filtering/boosting.
        """
        self._init_db()
        total_in_db = self.count()
        if total_in_db == 0:
            return []

        # Retrieve a broader pool if filtering is applied
        retrieve_k = min(top_k * 3 if (category or section) else top_k, total_in_db)

        query_embedding = campus_embedder.embed_query(query)
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=retrieve_k,
            include=["documents", "metadatas", "distances"]
        )

        matched_chunks = []
        if results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]

            for doc, meta, dist in zip(docs, metas, distances):
                # In cosine space: distance is 1 - cosine_similarity
                similarity_score = max(0.0, min(1.0, 1.0 - dist))
                
                # Check category & section matching
                passes_filter = True
                boost = 0.0

                if category and category != "All":
                    meta_cat = str(meta.get("category", "")).lower()
                    if category.lower() in meta_cat:
                        boost += 0.08
                    else:
                        passes_filter = False

                if section and section != "All":
                    meta_sec = str(meta.get("section", "")).lower()
                    meta_dept = str(meta.get("department", "")).lower()
                    sec_lower = section.lower()
                    if sec_lower in meta_sec or sec_lower in meta_dept:
                        boost += 0.12
                    else:
                        passes_filter = False

                # If caller strictly requested a section/category filter, respect it
                if (category and category != "All") or (section and section != "All"):
                    if not passes_filter:
                        continue

                adjusted_score = min(1.0, similarity_score + boost)
                matched_chunks.append({
                    "text": doc,
                    "metadata": meta,
                    "score": round(adjusted_score, 3)
                })

        # Sort by score descending and take top_k
        matched_chunks.sort(key=lambda x: x["score"], reverse=True)
        return matched_chunks[:top_k]

    def count(self) -> int:
        try:
            self._init_db()
            return self._collection.count()
        except Exception:
            return 0

    def reset(self):
        self._init_db()
        if self._client and self.collection_name:
            try:
                self._client.delete_collection(self.collection_name)
                self._collection = None
            except Exception:
                pass

_store_instance = None

def get_vector_store() -> CampusVectorStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = CampusVectorStore()
    return _store_instance
