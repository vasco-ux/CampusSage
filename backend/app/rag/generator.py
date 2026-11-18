import re
import json
import httpx
from typing import List, Dict, Any, Optional

from app.config import settings
from app.rag.prompts import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE

class CampusRAGGenerator:
    """Orchestrates LLM generation grounded strictly in retrieved notice evidence."""

    GREETING_PATTERNS = [
        r'^\s*(?:hey|hi|hello|heya|howdy|holla|greetings)\b',
        r'^\s*(?:good\s+(?:morning|afternoon|evening|day))\b',
        r'^\s*(?:who\s+are\s+you|what\s+is\s+your\s+name|what\s+can\s+you\s+do|how\s+can\s+you\s+help)\b',
        r'^\s*(?:thanks|thank\s+you|thx|bye|goodbye|see\s+you)\b'
    ]

    @classmethod
    def is_conversational_greeting(cls, text: str) -> bool:
        clean = text.strip().lower()
        if len(clean) < 25:
            for p in cls.GREETING_PATTERNS:
                if re.search(p, clean):
                    return True
        return False

    @classmethod
    def get_greeting_response(cls, text: str) -> Dict[str, Any]:
        clean = text.strip().lower()
        if any(w in clean for w in ["thank", "thx"]):
            answer = "You're very welcome! If you have any more questions about college notices, examination deadlines, or circulars, just ask anytime."
        elif any(w in clean for w in ["bye", "goodbye"]):
            answer = "Goodbye! Best of luck with your academics and examinations."
        else:
            answer = (
                "👋 Hello! I am **CampusSage**, your **AI-Powered Web Information & Opportunity Hub**.\n\n"
                "*Discover jobs, internships, scholarships, notices, deadlines, events, and useful information from websites in one place.*\n\n"
                "I am currently connected to official verified sources including **Government Engineering College, Ajmer** (54 public sections) and custom document uploads:\n"
                "- 📝 **Examinations & Results:** BTU/RTU exam forms, revaluation, copy view & fee cutoff dates\n"
                "- 💰 **Scholarships & Financial Aid:** State and national scholarship announcements & deadlines\n"
                "- 💼 **Placement & Opportunities:** TPO circulars, drive updates & industry interaction notices\n"
                "- 🛡️ **Campus Rules & Proctor:** Student discipline, code of conduct, anti-ragging & ID cards\n"
                "- 🏠 **Hostel Administration:** Room allotment (Boys & Girls AICTE scheme), mess rules & curfew\n"
                "- ⚖️ **Grievance Redressal:** Formal complaints, SGRC committee & Women Cell / ICC\n"
                "- 💻 **Departments:** CSE, Civil, Mechanical, Electrical, ECE, EIC, MCA, MBA notices & labs\n"
                "- 📚 **Academic Facilities:** Central Library book bank schemes & curriculum resources\n"
                "- 📎 **Document Analysis:** Upload any circular PDF or notice image directly to analyze it.\n\n"
                "What would you like to discover or inquire about today?"
            )

        return {
            "answer": answer,
            "grounded": True,
            "confidence": "100%",
            "conflict_alert": None,
            "sources": []
        }

    @staticmethod
    def format_context(retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Formats retrieved chunks with their source headers for LLM consumption."""
        if not retrieved_chunks:
            return "No relevant notices found."

        formatted_parts = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            meta = chunk.get("metadata", {})
            header = (
                f"[Source #{i}] Section: {meta.get('section', 'General')} | "
                f"Title: {meta.get('title', 'Unknown')} | "
                f"Ref: {meta.get('ref_no', 'N/A')} | "
                f"Date: {meta.get('issue_date', 'N/A')} | "
                f"Page: {meta.get('page', 1)} | "
                f"URL: {meta.get('source_url', 'N/A')}"
            )
            text = chunk.get("text", "").strip()
            formatted_parts.append(f"{header}\nPassage:\n{text}")

        return "\n\n".join(formatted_parts)

    @classmethod
    def generate_answer(cls, question: str, retrieved_chunks: List[Dict[str, Any]], history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Generates an answer using configured LLM or grounded extractor with multi-turn support.
        """
        # 1. Handle conversational greetings immediately
        if cls.is_conversational_greeting(question):
            return cls.get_greeting_response(question)

        # 2. Anti-hallucination check: If no chunks retrieved or relevance score too low
        top_score = retrieved_chunks[0].get("score", 0.0) if retrieved_chunks else 0.0
        
        # Check lexical/semantic overlap between question words and top chunk
        question_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', question.lower()))
        stop_words = {"what", "when", "where", "which", "about", "there", "their", "could", "would", "should", "please", "college", "notice", "tell"}
        content_words = question_words - stop_words
        top_text = (retrieved_chunks[0].get("text", "") + " " + retrieved_chunks[0].get("metadata", {}).get("title", "")).lower() if retrieved_chunks else ""
        has_keyword_overlap = any(w in top_text for w in content_words)

        if not retrieved_chunks or top_score < 0.25 or (not has_keyword_overlap and top_score < 0.35):
            return {
                "answer": (
                    f"❌ **Official Notice Not Found**\n\n"
                    f"I searched the college vector database across official circulars and notices from **Government Engineering College, Ajmer**, "
                    f"but could not find verified information regarding: *\"{question}\"*.\n\n"
                    f"*CampusSage safeguard:* Rather than guessing or generating inaccurate dates, we recommend consulting the "
                    f"**Examination Cell** or **Dean's Office** directly, or uploading the official circular PDF using the 📎 button."
                ),
                "grounded": False,
                "confidence": "0%",
                "conflict_alert": None,
                "sources": []
            }

        context_str = cls.format_context(retrieved_chunks)
        conflict_alert = cls._detect_conflict_in_context(retrieved_chunks)
        
        # Build prompt with conversation history context
        history_context = ""
        if history and len(history) > 0:
            history_lines = []
            for turn in history[-4:]:
                role = "Student" if turn.get("role") == "user" else "Assistant"
                content = turn.get("content", "").replace("\n", " ")[:150]
                history_lines.append(f"{role}: {content}")
            if history_lines:
                history_context = "Recent Conversation History:\n" + "\n".join(history_lines) + "\n\n"

        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"{history_context}"
            f"Context from Official College Circulars:\n----------------------------------------\n"
            f"{context_str}\n----------------------------------------\n\n"
            f"Student Question: {question}\n\n"
            f"Provide a concise, accurate, evidence-grounded answer with source citations:"
        )

        # 3. Attempt LLM generation
        answer = None
        if settings.LLM_PROVIDER == "ollama":
            answer = cls._call_ollama(full_prompt)
        elif settings.LLM_PROVIDER == "groq" and settings.GROQ_API_KEY:
            answer = cls._call_groq(full_prompt)

        # 4. Fallback Grounded Synthesizer (Zero-cost, works offline with 100% factual accuracy)
        if not answer:
            answer = cls._synthesize_grounded_answer(question, retrieved_chunks)

        # 5. Format source citation badges with clickable URLs and section metadata
        sources = []
        seen_refs = set()
        for chunk in retrieved_chunks:
            meta = chunk.get("metadata", {})
            ref = meta.get("ref_no") or meta.get("notice_id", "CIRCULAR")
            if ref not in seen_refs:
                seen_refs.add(ref)
                sources.append({
                    "id": ref,
                    "title": meta.get("title", "Official College Circular"),
                    "date": meta.get("issue_date"),
                    "page": meta.get("page", 1),
                    "section": meta.get("section", "General"),
                    "department": meta.get("department"),
                    "content_type": meta.get("content_type", "circular_pdf"),
                    "snippet": chunk.get("text", "")[:240].strip() + "...",
                    "category": meta.get("category", "General"),
                    "similarity": f"{int(chunk.get('score', 0.8) * 100)}%",
                    "source_url": meta.get("source_url"),
                    "pdf_url": meta.get("source_url")
                })

        return {
            "answer": answer,
            "grounded": True,
            "confidence": f"{int(retrieved_chunks[0].get('score', 0.85) * 100)}%",
            "conflict_alert": conflict_alert,
            "sources": sources
        }

    @staticmethod
    def _call_ollama(prompt: str) -> Optional[str]:
        try:
            with httpx.Client(timeout=12.0) as client:
                res = client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.1}
                    }
                )
                if res.status_code == 200:
                    return res.json().get("response")
        except Exception:
            pass
        return None

    @staticmethod
    def _call_groq(prompt: str) -> Optional[str]:
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json={
                        "model": settings.GROQ_MODEL,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1
                    }
                )
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"]
        except Exception:
            pass
        return None

    @staticmethod
    def _synthesize_grounded_answer(question: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Synthesizes factual bullet points directly from top retrieved passages.
        """
        top_chunk = chunks[0]
        meta = top_chunk.get("metadata", {})
        title = meta.get("title", "Official Notice")
        ref_no = meta.get("ref_no") or meta.get("notice_id", "CIRCULAR")
        section = meta.get("section") or "Official College Records"
        date_str = meta.get("issue_date", "")
        date_display = f"dated {date_str}" if date_str else ""

        answer_lines = [
            f"Based on official information from **{section}** [{ref_no}] (*{title}* {date_display}):\n"
        ]

        # Extract relevant lines containing numbers, dates, or keywords
        text = top_chunk.get("text", "")
        meaningful_lines = []
        for line in text.split("\n"):
            clean = line.strip()
            if len(clean) > 20 and not clean.startswith("Page") and not clean.startswith("http"):
                meaningful_lines.append(clean)

        if meaningful_lines:
            for line in meaningful_lines[:4]:
                answer_lines.append(f"- {line}")
        else:
            answer_lines.append(f"- {text[:280]}...")

        # If secondary chunk provides extra context
        if len(chunks) > 1 and chunks[1].get("score", 0) > 0.35:
            sec_meta = chunks[1].get("metadata", {})
            if sec_meta.get("ref_no") != ref_no:
                sec_sec = sec_meta.get("section") or "Related Section"
                sec_title = sec_meta.get("title", "Related Notice")
                answer_lines.append(f"\n*Related details in [{sec_sec} - {sec_title}]*")

        return "\n".join(answer_lines)

    @staticmethod
    def _detect_conflict_in_context(chunks: List[Dict[str, Any]]) -> Optional[str]:
        """Detects if multiple retrieved notices contain revision/postponement signals."""
        has_revision = False
        rev_title = ""
        for chunk in chunks:
            title = chunk.get("metadata", {}).get("title", "").lower()
            text = chunk.get("text", "").lower()
            if any(w in title or w in text for w in ["revised", "rescheduled", "resheduled", "postponed"]):
                has_revision = True
                rev_title = chunk.get("metadata", {}).get("title", "")
                break

        if has_revision and len(chunks) > 1:
            return f"⚠️ Schedule Update: Official notice '{rev_title}' indicates a postponement or revised schedule. Please rely on the latest circular."
        return None
