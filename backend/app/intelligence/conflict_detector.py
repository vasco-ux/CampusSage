import re
from typing import List, Dict, Any, Optional

class ConflictDetector:
    """
    Detects superseded circulars, rescheduled exams, and schedule revisions
    between earlier and newer notices using genuine document evidence.
    """

    REVISION_KEYWORDS = [
        "rescheduled", "resheduled", "revised", "postpone", "postponed",
        "preponed", "extension", "extended", "corrigendum", "amendment", "modification"
    ]

    @classmethod
    def detect_conflicts(cls, notices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        conflicts = []
        
        # Sort chronologically by issue date (newest first)
        sorted_notices = sorted(notices, key=lambda n: n.get("issue_date") or "", reverse=True)

        for i, newer in enumerate(sorted_notices):
            newer_text = (newer.get("full_text") or "").lower()
            newer_title = (newer.get("title") or "").lower()

            # Check if this notice explicitly announces a revision or rescheduling
            is_revision = any(w in newer_title or w in newer_text[:300] for w in cls.REVISION_KEYWORDS)
            if not is_revision:
                continue

            # Topic extraction helper
            def extract_topic_keywords(text: str) -> List[str]:
                tokens = []
                for kw in ["7th sem", "vii sem", "3rd sem", "iii sem", "5th sem", "v sem", "practical", "theory", "reval", "exam form", "convocation", "time table", "tuition fee"]:
                    if kw in text:
                        tokens.append(kw)
                return tokens

            newer_topics = extract_topic_keywords(newer_title + " " + newer_text[:300])

            # Look for an earlier notice matching the same topic
            matched_earlier = None
            for older in sorted_notices[i+1:]:
                older_text = (older.get("full_text") or "").lower()
                older_title = (older.get("title") or "").lower()

                # Check if older notice shares key topic keywords
                older_topics = extract_topic_keywords(older_title + " " + older_text[:300])
                shared = set(newer_topics).intersection(set(older_topics))
                
                if shared or (newer.get("category") == older.get("category") and any(w in newer_title and w in older_title for w in ["practical", "exam", "revaluation", "fee"])):
                    matched_earlier = older
                    break

            if matched_earlier:
                conflicts.append({
                    "id": f"CONF-{newer['id']}-{matched_earlier['id']}",
                    "topic": f"Schedule Revision: {newer.get('title')[:60]}",
                    "severity": "high",
                    "original_notice_id": matched_earlier.get("id"),
                    "superseding_notice_id": newer.get("id"),
                    "original_date": matched_earlier.get("issue_date"),
                    "revised_date": newer.get("issue_date"),
                    "resolution": f"Official notice '{newer.get('title')}' officially supersedes schedule in prior circular '{matched_earlier.get('title')}'. Always follow the latest circular.",
                    "evidence": {
                        "newer_title": newer.get("title"),
                        "newer_ref": newer.get("ref_no"),
                        "newer_pdf": newer.get("source_url"),
                        "older_title": matched_earlier.get("title"),
                        "older_ref": matched_earlier.get("ref_no"),
                        "older_pdf": matched_earlier.get("source_url")
                    }
                })
            else:
                # Standalone rescheduling notice (e.g. Rescheduled Practical Exam)
                conflicts.append({
                    "id": f"CONF-{newer['id']}-REV",
                    "topic": f"Schedule Modification: {newer.get('title')[:60]}",
                    "severity": "medium",
                    "original_notice_id": "Prior Schedule",
                    "superseding_notice_id": newer.get("id"),
                    "original_date": "Prior Circular",
                    "revised_date": newer.get("issue_date"),
                    "resolution": f"Notice '{newer.get('title')}' announces revised dates. Please verify updated timetable in the attached circular PDF.",
                    "evidence": {
                        "newer_title": newer.get("title"),
                        "newer_ref": newer.get("ref_no"),
                        "newer_pdf": newer.get("source_url")
                    }
                })

        return conflicts
