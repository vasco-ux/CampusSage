import re
from typing import List, Dict, Any
from datetime import datetime

class DeadlineExtractor:
    """
    Extracts verified academic deadlines, cutoff dates, and exam milestones
    from college notice titles and text.
    """

    MONTHS = r"January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
    
    # Milestone keywords
    EVENT_KEYWORDS = [
        "last date", "deadline", "submission", "commence", "commencement",
        "examination form", "exam form", "fee payment", "single fee", "double fee",
        "revaluation", "copy view", "registration", "convocation", "updation"
    ]

    DATE_PATTERNS = [
        # DD.MM.YYYY or DD/MM/YYYY or DD-MM-YYYY
        r'\b(\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{4})\b',
        # DD Month YYYY (e.g. 1 November 2026, 12th Oct 2026)
        rf'\b(\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{MONTHS})\s+\d{{4}})\b',
        # Month DD, YYYY (e.g. November 1, 2026)
        rf'\b((?:{MONTHS})\s+\d{{1,2}},?\s+\d{{4}})\b'
    ]

    @classmethod
    def _parse_and_validate_date(cls, raw_date_str: str) -> str:
        """Standardizes date to DD.MM.YYYY or returns empty string if invalid."""
        raw = raw_date_str.strip().rstrip(".,)")
        # Try DD.MM.YYYY / DD/MM/YYYY / DD-MM-YYYY
        for sep in [".", "/", "-"]:
            if sep in raw and not any(c.isalpha() for c in raw):
                parts = raw.split(sep)
                if len(parts) == 3:
                    try:
                        d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                        if 1 <= d <= 31 and 1 <= m <= 12 and 2024 <= y <= 2028:
                            return f"{d:02d}.{m:02d}.{y}"
                    except ValueError:
                        pass
        
        # Try text date (e.g. 1 November 2026)
        clean_text_date = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', raw)
        for fmt in ["%d %B %Y", "%d %b %Y", "%B %d %Y", "%B %d, %Y", "%b %d %Y", "%b %d, %Y"]:
            try:
                dt = datetime.strptime(clean_text_date, fmt)
                if 2024 <= dt.year <= 2028:
                    return dt.strftime("%d.%m.%Y")
            except ValueError:
                continue

        return raw

    @classmethod
    def extract_deadlines_from_notice(cls, notice: Dict[str, Any]) -> List[Dict[str, Any]]:
        title = notice.get("title", "")
        text = notice.get("full_text") or notice.get("summary") or ""
        source_url = notice.get("source_url")
        pdf_path = notice.get("pdf_path")
        deadlines = []
        seen_keys = set()
        idx = 1

        # 1. Check notice TITLE first for explicit last dates
        # E.g. "Circular for revaluation ... (Last date 12.11.2026)" or "Last date with single fee 1 November 2026"
        for pattern in cls.DATE_PATTERNS:
            for match in re.finditer(pattern, title, re.IGNORECASE):
                raw_date = match.group(1)
                valid_date = cls._parse_and_validate_date(raw_date)
                if valid_date:
                    clean_title = re.sub(r'\(?\s*(?:last date|deadline)[^\)]*\)?', '', title, flags=re.IGNORECASE).strip(" -:")
                    if len(clean_title) < 15:
                        clean_title = title[:75]
                    
                    key = (notice.get("id"), valid_date)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        deadlines.append({
                            "id": f"DL-{notice.get('id')}-{idx}",
                            "title": clean_title[:90],
                            "deadline_date": valid_date,
                            "category": notice.get("category", "Examinations"),
                            "section": notice.get("section"),
                            "department": notice.get("department"),
                            "source_notice_id": notice.get("id"),
                            "source_title": title,
                            "source_url": source_url,
                            "pdf_path": pdf_path,
                            "notes": f"Official deadline specified in notice title: {title[:90]}",
                            "urgency": "upcoming",
                            "is_active": 1
                        })
                        idx += 1

        # 2. Check full text lines
        lines = text.split("\n")
        for line in lines:
            line_clean = line.strip()
            lower = line_clean.lower()

            if any(k in lower for k in cls.EVENT_KEYWORDS):
                for pattern in cls.DATE_PATTERNS:
                    date_match = re.search(pattern, line_clean, re.IGNORECASE)
                    if date_match:
                        raw_date = date_match.group(1)
                        valid_date = cls._parse_and_validate_date(raw_date)
                        if not valid_date:
                            continue

                        key = (notice.get("id"), valid_date)
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)

                        # Clean description
                        clean_desc = line_clean[:85].strip(" -:1234567890.*#")
                        if len(clean_desc) < 15 or "last date" in clean_desc.lower():
                            clean_desc = f"{title[:60]} (Milestone)"

                        deadlines.append({
                            "id": f"DL-{notice.get('id')}-{idx}",
                            "title": clean_desc,
                            "deadline_date": valid_date,
                            "category": notice.get("category", "Examinations"),
                            "section": notice.get("section"),
                            "department": notice.get("department"),
                            "source_notice_id": notice.get("id"),
                            "source_title": title,
                            "source_url": source_url,
                            "pdf_path": pdf_path,
                            "notes": line_clean[:140],
                            "urgency": "upcoming",
                            "is_active": 1
                        })
                        idx += 1
                        break

        return deadlines
