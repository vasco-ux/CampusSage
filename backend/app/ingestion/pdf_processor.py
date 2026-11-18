import pymupdf as fitz
import re
import os
from typing import List, Dict, Any

class PDFProcessor:
    """Extracts clean text, page numbers, and metadata from college circular PDFs using PyMuPDF."""

    @staticmethod
    def extract_text_and_pages(pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text from each page of a PDF document.
        Returns a list of page dicts: [{'page_number': 1, 'text': '...'}]
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found at: {pdf_path}")

        pages_data = []
        doc = fitz.open(pdf_path)
        try:
            for page_index in range(len(doc)):
                page = doc[page_index]
                text = page.get_text("text")
                # Clean extraneous whitespace while preserving line structures
                cleaned_text = PDFProcessor._clean_text(text)
                if cleaned_text:
                    pages_data.append({
                        "page_number": page_index + 1,
                        "text": cleaned_text
                    })
        finally:
            doc.close()

        return pages_data

    @staticmethod
    def extract_metadata_from_text(text: str) -> Dict[str, Any]:
        """Heuristically extracts reference numbers, dates, and categories from circular text."""
        metadata = {
            "ref_no": None,
            "date": None,
            "category": "General"
        }

        # 1. Regex for Reference Numbers (e.g., Ref. No: COE/EXAM/2026/89 or Ref: ACAD/102)
        ref_match = re.search(r'(?:Ref\.?\s*(?:No\.?)?[:\-\s]+)([A-Z0-9\/\-\.]+)', text, re.IGNORECASE)
        if ref_match:
            metadata["ref_no"] = ref_match.group(1).strip()

        # 2. Regex for Dates (e.g. October 28, 2026 or 28-10-2026 or 28/10/2026)
        date_match = re.search(r'(?:Date[:\-\s]+)?((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}|\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})', text, re.IGNORECASE)
        if date_match:
            metadata["date"] = date_match.group(1).strip()

        # 3. Category Detection
        lower_text = text.lower()
        if any(w in lower_text for w in ["exam", "examination", "admit card", "coe", "grade", "backlog"]):
            metadata["category"] = "Examinations"
        elif any(w in lower_text for w in ["fee", "dues", "tuition", "fine", "accounts"]):
            metadata["category"] = "Fees"
        elif any(w in lower_text for w in ["placement", "recruitment", "tpo", "tcs", "infosys", "drive"]):
            metadata["category"] = "Placements"
        elif any(w in lower_text for w in ["conference", "syllabus", "lecture", "holiday", "academic calendar"]):
            metadata["category"] = "Academics"

        return metadata

    @staticmethod
    def _clean_text(text: str) -> str:
        """Removes abnormal whitespace, null bytes, and fixes basic hyphenation."""
        if not text:
            return ""
        # Remove null characters
        text = text.replace("\x00", "")
        # Normalize multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Strip trailing whitespaces per line
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(lines).strip()
