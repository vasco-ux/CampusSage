from typing import List, Dict, Any
import re

class NoticeChunker:
    """
    Splits long notice texts into semantic, overlapping chunks 
    while preserving document-level metadata (notice ID, title, date, page).
    """

    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 120):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_notice_pages(self, notice: Dict[str, Any], pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes notice metadata and a list of page objects, returns chunks with enriched metadata.
        """
        all_chunks = []
        chunk_idx = 0

        for page in pages:
            page_num = page.get("page_number", 1)
            text = page.get("text", "").strip()
            if not text:
                continue

            raw_chunks = self._recursive_split(text, self.chunk_size, self.chunk_overlap)

            for rc in raw_chunks:
                chunk_id = f"{notice['id']}-p{page_num}-c{chunk_idx}"
                all_chunks.append({
                    "id": chunk_id,
                    "text": rc,
                    "metadata": {
                        "notice_id": notice.get("id"),
                        "ref_no": notice.get("ref_no") or "",
                        "title": notice.get("title") or "",
                        "issue_date": notice.get("issue_date") or "",
                        "category": notice.get("category") or "General",
                        "section": notice.get("section") or "",
                        "department": notice.get("department") or "",
                        "content_type": notice.get("content_type") or "pdf",
                        "page": page_num,
                        "source_url": notice.get("source_url") or "",
                        "chunk_index": chunk_idx
                    }
                })
                chunk_idx += 1

        return all_chunks

    def _recursive_split(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Splits text preferentially on double newlines, then newlines, then periods, then spaces."""
        if len(text) <= chunk_size:
            return [text]

        separators = ["\n\n", "\n", ". ", " "]
        for sep in separators:
            splits = text.split(sep)
            chunks = []
            current = ""
            for s in splits:
                candidate = (current + sep + s) if current else s
                if len(candidate) <= chunk_size:
                    current = candidate
                else:
                    if current:
                        chunks.append(current.strip())
                    current = s
            if current:
                chunks.append(current.strip())

            if len(chunks) > 1:
                return chunks

        # Fallback hard chunking with overlap
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end].strip())
            if end == len(text):
                break
            start += (chunk_size - chunk_overlap)
        return chunks
