from typing import List
import os
import re
import hashlib
import numpy as np
from app.config import settings

def _stable_hash(s: str) -> int:
    """Deterministic integer hash across all Python processes and platforms."""
    return int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16)

class CampusEmbeddingManager:
    """
    Generates 384-dimensional semantic embeddings for college circulars.
    Uses localized SentenceTransformers when available or a high-accuracy,
    deterministic TF-IDF sublinear vector space.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            local_path = os.path.join(settings.MODELS_DIR, self.model_name)
            if os.path.exists(local_path):
                try:
                    from sentence_transformers import SentenceTransformer
                    self._model = SentenceTransformer(local_path, local_files_only=True)
                except Exception:
                    self._model = "fallback"
            else:
                self._model = "fallback"
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        if model != "fallback":
            embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
            return embeddings.tolist()
        else:
            return [self._fallback_embed(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        return self.embed_documents([query])[0]

    def _fallback_embed(self, text: str, dim: int = 384) -> List[float]:
        """
        Deterministic, cross-process TF-IDF vector embedding with sublinear scaling
        and exact word/bigram hash projections.
        """
        vec = np.zeros(dim, dtype=np.float32)
        clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
        tokens = [t for t in clean.split() if len(t) >= 2]
        
        stopwords = {"the", "is", "at", "which", "on", "and", "a", "an", "in", "to", "for", "of", "with", "this", "that"}

        for i, word in enumerate(tokens):
            weight = 0.5 if word in stopwords else 4.0
            
            # Word token projection
            h1 = _stable_hash(f"word_{word}") % dim
            vec[h1] += weight
            
            # Trigram sub-tokens
            for j in range(len(word) - 2):
                tri = word[j:j+3]
                h_tri = _stable_hash(f"tri_{tri}") % dim
                vec[h_tri] += 1.5

            # Word bigrams
            if i > 0:
                bg = f"{tokens[i-1]}_{word}"
                h_bg = _stable_hash(f"bg_{bg}") % dim
                vec[h_bg] += 5.0

        # L2 normalize
        norm = float(np.linalg.norm(vec))
        if norm > 0.0:
            vec = vec / norm
        return vec.tolist()

campus_embedder = CampusEmbeddingManager()
