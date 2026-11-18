import os
import re
import requests
import urllib.robotparser
import urllib.parse
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Tuple

from app.config import settings
from app.ingestion.pdf_processor import PDFProcessor
from app.ingestion.sections_catalog import (
    ALL_SECTIONS,
    SECTIONS_BY_SLUG,
    get_section_by_slug,
    find_section_by_url
)

class NoticeScraper:
    """
    Universal multi-section ingestion engine for Government Engineering College, Ajmer.
    Features:
    - Covers all 36 public cells, 13 academic departments, Principal office, and disclosures.
    - Dual ingestion: HTML landing page informational content + downloadable PDF circulars.
    - Deduplication: avoids duplicate chunks and downloads.
    - Robots.txt compliance validation.
    - Comprehensive diagnostic execution logs.
    """

    NOTICE_KEYWORDS = [
        "notice", "circular", "exam", "examination", "schedule", "deadline",
        "academic", "result", "fee", "notification", "admission", "tpo",
        "placement", "postpone", "revised", "announcement", "convocation",
        "proctor", "hostel", "scholarship", "syllabus", "grievance", "timetable"
    ]

    def __init__(self, timeout: int = 12):
        self.timeout = (3.5, float(timeout))
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 CampusSage/2.0",
            "Accept": "application/json, text/html, application/xhtml+xml, application/xml;q=0.9, application/pdf, */*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self.logs: List[str] = []

    def log(self, level: str, message: str):
        entry = f"[{level}] {message}"
        self.logs.append(entry)
        print(entry)

    def check_robots_allowed(self, target_url: str) -> Tuple[bool, str]:
        """Validates robots.txt compliance and returns (is_allowed, reason)."""
        parsed = urlparse(target_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        
        try:
            self.log("INFO", f"Checking robots.txt at {robots_url}...")
            resp = self.session.get(robots_url, timeout=(3.0, 5.0), verify=False)
            if resp.status_code == 200:
                if "<html" in resp.text.lower() or "<!doctype" in resp.text.lower():
                    self.log("INFO", "robots.txt rewritten by SPA server to index.html. Access permitted under public web etiquette.")
                    return True, "SPA default fallback on robots.txt"
                
                rp.parse(resp.text.splitlines())
                allowed = rp.can_fetch(self.session.headers["User-Agent"], target_url)
                if not allowed:
                    reason = f"Explicitly disallowed by robots.txt rules on {parsed.netloc}"
                    self.log("WARNING", reason)
                    return False, reason
                self.log("INFO", f"Robots.txt check passed: Access allowed for {target_url}")
                return True, "Allowed by robots.txt"
            elif resp.status_code == 404:
                self.log("INFO", "No robots.txt found (HTTP 404). Proceeding under public access.")
                return True, "No robots.txt restriction"
            else:
                self.log("INFO", f"robots.txt returned status {resp.status_code}. Proceeding respectfully.")
                return True, f"HTTP {resp.status_code} on robots.txt"
        except Exception as e:
            self.log("INFO", f"robots.txt check ({e}). Proceeding under standard public web etiquette.")
            return True, "robots.txt unreachable"

    def is_pdf_url(self, url: str) -> bool:
        clean_url = url.split("?")[0].lower()
        return clean_url.endswith(".pdf")

    def scrape_notices_from_url(self, target_url: str, max_items: int = 8) -> List[Dict[str, Any]]:
        """
        Main discovery router. Automatically maps URL to the relevant section or runs crawler.
        """
        self.logs = []
        self.log("INFO", f"Initiating website ingestion for: {target_url}")

        allowed, reason = self.check_robots_allowed(target_url)
        if not allowed:
            self.log("WARNING", f"Crawling halted: {reason}")
            return []

        # Check if URL maps to a known GEC Ajmer section
        matched_section = find_section_by_url(target_url)
        if matched_section:
            self.log("INFO", f"Matched target URL to official section: '{matched_section['name']}' ({matched_section['slug']})")
            return self.scrape_section(matched_section, max_items=max_items)

        # Route 1: Generic GEC Ajmer crawl
        if "ecajmer.ac.in" in target_url:
            return self._scrape_gec_ajmer(target_url, max_items)

        # Route 2: Direct PDF file
        if self.is_pdf_url(target_url):
            self.log("INFO", f"Target is a direct PDF circular: {target_url}")
            notice = self._process_single_pdf_url(target_url, "Direct Notice Circular", "College Portal")
            return [notice] if notice else []

        # Route 3: Generic HTML College Notice Board
        return self._scrape_generic_html_portal(target_url, max_items)

    def scrape_section(self, section: Dict[str, Any], max_items: int = 5) -> List[Dict[str, Any]]:
        """
        Ingests both landing page informational text and circular PDFs for a specific section.
        """
        slug = section.get("slug")
        sec_type = section.get("type", "cell")
        name = section.get("name", slug)
        category = section.get("category", "General")
        public_url = section.get("public_url", f"https://www.ecajmer.ac.in/ui/cells/{slug}")
        dept_name = name if sec_type == "department" else None

        self.log("INFO", f"--- Starting ingestion for section: [{name}] (Type: {sec_type}, Category: {category}) ---")

        if sec_type == "special":
            return self._scrape_special_section(section, max_items)

        return self._scrape_cell_or_dept(
            slug=slug,
            sec_type=sec_type,
            section_name=name,
            category=category,
            public_url=public_url,
            department_name=dept_name,
            max_items=max_items
        )

    def scrape_all_sections(self, sections: Optional[List[Dict[str, Any]]] = None, max_per_section: int = 3) -> List[Dict[str, Any]]:
        """
        Crawls all official college sections systematically.
        """
        target_sections = sections or ALL_SECTIONS
        self.logs = []
        self.log("INFO", f"Starting College-Wide Multi-Section Ingestion across {len(target_sections)} sections...")
        
        all_notices = []
        for sec in target_sections:
            try:
                sec_notices = self.scrape_section(sec, max_items=max_per_section)
                all_notices.extend(sec_notices)
            except Exception as e:
                self.log("ERROR", f"Failed section {sec.get('name')}: {e}")

        self.log("INFO", f"College-wide ingestion complete! Total items harvested: {len(all_notices)}")
        return all_notices

    def _scrape_cell_or_dept(
        self,
        slug: str,
        sec_type: str,
        section_name: str,
        category: str,
        public_url: str,
        department_name: Optional[str] = None,
        max_items: int = 5
    ) -> List[Dict[str, Any]]:
        """Ingests landing about text + latest circular PDFs for a cell or department."""
        notices: List[Dict[str, Any]] = []

        # 1. Harvest Landing Page About / Guidelines Text
        about_notice = self._scrape_landing_about(
            slug=slug,
            sec_type=sec_type,
            section_name=section_name,
            category=category,
            public_url=public_url,
            department_name=department_name
        )
        if about_notice:
            notices.append(about_notice)

        # 2. Harvest Circular PDFs from Section API
        circular_api = f"https://ecajmer.ac.in/api/circulars/public/{slug}?page=1&limit={max_items}&mainCategoryId=1"
        self.log("INFO", f"Checking circulars API: {circular_api}")

        try:
            resp = self.session.get(circular_api, timeout=self.timeout, verify=False)
            if resp.status_code == 200:
                res_json = resp.json()
                items = res_json.get("data", [])
                if isinstance(items, dict):
                    items = [items]
                self.log("INFO", f"Discovered {len(items)} circular items in [{section_name}]")

                for item in items[:max_items]:
                    title = item.get("title", "").strip()
                    content_path = item.get("content", "")
                    content_type = item.get("contentType", "").lower()

                    if not content_path or (content_type != "pdf" and not content_path.lower().endswith(".pdf")):
                        self.log("SKIPPED", f"[{section_name}] Notice '{title[:40]}' has no PDF attachment.")
                        continue

                    encoded_path = urllib.parse.quote(content_path)
                    full_pdf_url = f"https://ecajmer.ac.in/{encoded_path}"
                    sno = item.get("sno") or f"GECA-{slug.upper()}-{item.get('id', 'N/A')}"
                    issue_date = item.get("date") or (item.get("createdAt", "")[:10] if item.get("createdAt") else None)

                    notice_obj = self._download_and_parse_gec_pdf(
                        pdf_url=full_pdf_url,
                        title=title,
                        sno=sno,
                        issue_date=issue_date,
                        category=category,
                        section_name=section_name,
                        department_name=department_name
                    )
                    if notice_obj:
                        notices.append(notice_obj)
                        self.log("SUCCESS", f"[{section_name}] Indexed PDF '{title[:45]}' ({notice_obj['chunks_count']} chunks)")
            else:
                self.log("INFO", f"[{section_name}] Circulars endpoint returned HTTP {resp.status_code}")
        except Exception as e:
            self.log("ERROR", f"[{section_name}] Error querying circulars API: {e}")

        return notices

    def _scrape_landing_about(
        self,
        slug: str,
        sec_type: str,
        section_name: str,
        category: str,
        public_url: str,
        department_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Harvests landing descriptive HTML and policies from public API."""
        about_api = f"https://ecajmer.ac.in/api/public/landingAbout/{slug}?type={sec_type}"
        self.log("INFO", f"Fetching landing information: {about_api}")

        try:
            resp = self.session.get(about_api, timeout=self.timeout, verify=False)
            if resp.status_code != 200:
                self.log("INFO", f"No landing about text found for [{slug}] (HTTP {resp.status_code})")
                return None

            data = resp.json().get("data")
            if not data:
                return None

            raw_html_pieces = []
            
            def extract_html(obj):
                if isinstance(obj, str):
                    raw_html_pieces.append(obj)
                elif isinstance(obj, dict):
                    for k in ["description", "content", "about", "detail", "Celldetail", "Hod_AboutUs", "objective", "pmessage"]:
                        if k in obj and obj[k]:
                            extract_html(obj[k])
                elif isinstance(obj, list):
                    for item in obj:
                        extract_html(item)

            if isinstance(data, dict):
                extract_html(data.get("Celldetail"))
                extract_html(data.get("Hod_AboutUs"))
                extract_html(data.get("about"))
                extract_html(data.get("description"))
                extract_html(data.get("detail"))
                extract_html(data.get("objective"))
            elif isinstance(data, list):
                for item in data:
                    extract_html(item)
            elif isinstance(data, str):
                raw_html_pieces.append(data)

            raw_html = "\n".join(raw_html_pieces).strip()
            if not raw_html or len(raw_html) < 25:
                return None

            # Clean HTML to readable plain text
            soup = BeautifulSoup(raw_html, "html.parser")
            clean_text = soup.get_text("\n", strip=True)

            if len(clean_text) < 35:
                return None

            doc_title = f"{section_name}: Official Overview, Guidelines & Objectives"
            doc_id = f"PAGE-{slug.upper()}-ABOUT"

            self.log("SUCCESS", f"[{section_name}] Extracted official webpage overview ({len(clean_text)} chars)")

            return {
                "id": doc_id,
                "ref_no": f"INFO/{slug.upper()}",
                "title": doc_title,
                "issue_date": None,
                "category": category,
                "section": section_name,
                "department": department_name,
                "content_type": "webpage",
                "summary": clean_text[:400].strip() + "..." if len(clean_text) > 400 else clean_text,
                "full_text": clean_text,
                "pdf_path": None,
                "source_url": public_url,
                "source_institution": "Government Engineering College, Ajmer",
                "status": f"Active ({section_name} Official Webpage)",
                "page_count": 1,
                "chunks_count": 0,
                "_pages": [{"page_number": 1, "text": clean_text}]
            }

        except Exception as e:
            self.log("ERROR", f"Failed to fetch landing about for [{slug}]: {e}")
            return None

    def _scrape_special_section(self, section: Dict[str, Any], max_items: int = 5) -> List[Dict[str, Any]]:
        """Handles special endpoints such as Principal message, mandatory disclosures, achievements."""
        slug = section["slug"]
        name = section["name"]
        category = section["category"]
        endpoint = section.get("endpoint")
        public_url = section.get("public_url", "https://www.ecajmer.ac.in")

        notices = []
        self.log("INFO", f"Scraping special institutional endpoint: {endpoint}")

        try:
            resp = self.session.get(endpoint, timeout=self.timeout, verify=False)
            if resp.status_code != 200:
                self.log("WARNING", f"Endpoint {endpoint} returned HTTP {resp.status_code}")
                return []

            res_json = resp.json()
            data = res_json.get("data")

            # Case A: Principal Message
            if slug == "principal" and data:
                item = data[0] if isinstance(data, list) and data else (data if isinstance(data, dict) else {})
                principal_name = item.get("pname") or item.get("name") or "Dr. Radha Kishan Motwani"
                designation = item.get("designation") or "Principal"
                message_html = item.get("pmessage") or item.get("message") or ""
                highlight_html = item.get("phighlightedmessage") or ""
                soup = BeautifulSoup(message_html + "\n" + highlight_html, "html.parser")
                clean_msg = soup.get_text("\n", strip=True)

                doc_text = (
                    f"Government Engineering College, Ajmer\n"
                    f"Official Message & Vision from the Principal ({principal_name}, {designation}):\n\n"
                    f"{clean_msg}"
                )
                notices.append({
                    "id": "INST-PRINCIPAL-MESSAGE",
                    "ref_no": "PRIN/MSG/OFFICIAL",
                    "title": f"Principal's Address to Students & Institutional Vision ({principal_name})",
                    "issue_date": None,
                    "category": "Administration",
                    "section": name,
                    "department": None,
                    "content_type": "webpage",
                    "summary": doc_text[:400].strip() + "...",
                    "full_text": doc_text,
                    "pdf_path": None,
                    "source_url": public_url,
                    "source_institution": "Government Engineering College, Ajmer",
                    "status": "Active (Official Principal Message)",
                    "page_count": 1,
                    "chunks_count": 0,
                    "_pages": [{"page_number": 1, "text": doc_text}]
                })
                self.log("SUCCESS", f"Indexed Principal's official message ({len(doc_text)} chars)")

            # Case B: Mandatory Disclosures & NBA Accreditation
            elif slug == "mandatory-disclosures" and data:
                items = data if isinstance(data, list) else [data]
                disclosure_texts = []
                for it in items[:15]:
                    title = it.get("title") or it.get("name") or "Statutory Institutional Disclosure"
                    link = it.get("file") or it.get("content") or ""
                    disclosure_texts.append(f"• {title} (URL: https://ecajmer.ac.in/{link})")

                if disclosure_texts:
                    full_disc = (
                        "Government Engineering College, Ajmer - Mandatory Disclosures & AICTE Approvals:\n\n"
                        + "\n".join(disclosure_texts)
                    )
                    notices.append({
                        "id": "INST-MANDATORY-DISCLOSURES",
                        "ref_no": "INST/AICTE/NBA/DISC",
                        "title": "Mandatory Disclosures, AICTE Approvals & NBA Accreditation",
                        "issue_date": None,
                        "category": "Administration",
                        "section": name,
                        "department": None,
                        "content_type": "webpage",
                        "summary": full_disc[:400].strip() + "...",
                        "full_text": full_disc,
                        "pdf_path": None,
                        "source_url": public_url,
                        "source_institution": "Government Engineering College, Ajmer",
                        "status": "Active (Statutory Disclosure)",
                        "page_count": 1,
                        "chunks_count": 0,
                        "_pages": [{"page_number": 1, "text": full_disc}]
                    })
                    self.log("SUCCESS", f"Indexed {len(disclosure_texts)} mandatory disclosures")

            # Case C: Student & Institutional Achievements
            elif slug == "achievements" and data:
                items = data if isinstance(data, list) else [data]
                ach_lines = []
                for it in items[:15]:
                    t = it.get("title") or it.get("name") or ""
                    d = it.get("description") or ""
                    ach_lines.append(f"• {t}: {d}")

                if ach_lines:
                    full_ach = "Government Engineering College, Ajmer - Student & Campus Achievements:\n\n" + "\n".join(ach_lines)
                    notices.append({
                        "id": "INST-ACHIEVEMENTS",
                        "ref_no": "STUDENT/ACHIEVEMENTS",
                        "title": "GEC Ajmer Student Achievements, Hackathon Honors & Sports Awards",
                        "issue_date": None,
                        "category": "Student Welfare & Activities",
                        "section": name,
                        "department": None,
                        "content_type": "webpage",
                        "summary": full_ach[:400].strip() + "...",
                        "full_text": full_ach,
                        "pdf_path": None,
                        "source_url": public_url,
                        "source_institution": "Government Engineering College, Ajmer",
                        "status": "Active (Student Achievements)",
                        "page_count": 1,
                        "chunks_count": 0,
                        "_pages": [{"page_number": 1, "text": full_ach}]
                    })
                    self.log("SUCCESS", f"Indexed {len(ach_lines)} student achievements")

            # Case D: Academic Calendar / TPO Circulars
            elif slug in ["academic-calendar", "tpo-placement"] and data:
                items = data if isinstance(data, list) else [data]
                for item in items[:max_items]:
                    title = item.get("title", "").strip()
                    content_path = item.get("content", "")
                    if content_path and content_path.lower().endswith(".pdf"):
                        full_pdf_url = f"https://ecajmer.ac.in/{urllib.parse.quote(content_path)}"
                        sno = item.get("sno") or f"GECA-{slug.upper()}-{item.get('id', 'N/A')}"
                        issue_date = item.get("date") or (item.get("createdAt", "")[:10] if item.get("createdAt") else None)
                        notice_obj = self._download_and_parse_gec_pdf(
                            pdf_url=full_pdf_url,
                            title=title,
                            sno=sno,
                            issue_date=issue_date,
                            category=category,
                            section_name=name
                        )
                        if notice_obj:
                            notices.append(notice_obj)
                            self.log("SUCCESS", f"[{name}] Indexed circular PDF '{title[:45]}'")

        except Exception as e:
            self.log("ERROR", f"Error scraping special section [{name}]: {e}")

        return notices

    def _scrape_gec_ajmer(self, target_url: str, max_items: int = 8) -> List[Dict[str, Any]]:
        """Fallback crawler for general GEC Ajmer endpoints."""
        self.log("INFO", "Executing default GEC Ajmer notice bar crawler...")
        notices: List[Dict[str, Any]] = []

        endpoints = [
            ("https://ecajmer.ac.in/api/circulars/public/examination-section?page=1&limit=10&mainCategoryId=1", "Examination Section", "Examinations"),
            ("https://ecajmer.ac.in/api/circulars/public/notice-bar/hero", "General Notice Bar", "Academic"),
            ("https://ecajmer.ac.in/api/circulars/public/proctor?page=1&limit=5&mainCategoryId=1", "Proctor Section", "Proctor & Student Welfare")
        ]

        seen_titles = set()

        for ep, sec_name, cat in endpoints:
            if len(notices) >= max_items:
                break
            try:
                self.log("INFO", f"Visiting API: {ep}")
                resp = self.session.get(ep, timeout=self.timeout, verify=False)
                if resp.status_code != 200:
                    continue

                items = resp.json().get("data", [])
                if isinstance(items, dict):
                    items = [items]

                for item in items:
                    if len(notices) >= max_items:
                        break
                    title = item.get("title", "").strip()
                    if not title or title.lower() in seen_titles:
                        continue
                    seen_titles.add(title.lower())

                    content_path = item.get("content", "")
                    content_type = item.get("contentType", "").lower()

                    if not content_path or (content_type != "pdf" and not content_path.lower().endswith(".pdf")):
                        continue

                    full_pdf_url = f"https://ecajmer.ac.in/{urllib.parse.quote(content_path)}"
                    sno = item.get("sno") or f"GECA-{item.get('id', 'N/A')}"
                    issue_date = item.get("date") or (item.get("createdAt", "")[:10] if item.get("createdAt") else None)

                    notice_obj = self._download_and_parse_gec_pdf(
                        pdf_url=full_pdf_url,
                        title=title,
                        sno=sno,
                        issue_date=issue_date,
                        category=cat,
                        section_name=sec_name
                    )
                    if notice_obj:
                        notices.append(notice_obj)
            except Exception as e:
                self.log("ERROR", f"Error in general crawler {ep}: {e}")

        return notices

    def _download_and_parse_gec_pdf(
        self,
        pdf_url: str,
        title: str,
        sno: str,
        issue_date: Optional[str],
        category: str,
        section_name: str = "General",
        department_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Downloads a PDF from GEC Ajmer and extracts page-by-page text via PyMuPDF."""
        try:
            resp = self.session.get(pdf_url, timeout=(3.5, 15.0), verify=False)
            if resp.status_code != 200 or len(resp.content) < 400:
                self.log("SKIPPED", f"PDF at {pdf_url} returned HTTP {resp.status_code} or is empty.")
                return None

            clean_sno = re.sub(r'[^a-zA-Z0-9_\-]', '_', sno)
            safe_filename = f"{clean_sno}_{abs(hash(title)) % 10000}.pdf"
            local_pdf_path = os.path.join(settings.PDF_DIR, safe_filename)

            with open(local_pdf_path, "wb") as f:
                f.write(resp.content)

            # PyMuPDF extraction
            pages = PDFProcessor.extract_text_and_pages(local_pdf_path)
            if not pages or not any(p["text"].strip() for p in pages):
                # Fallback for scanned image PDFs: generate structured text from title, sno, date and section
                self.log("INFO", f"[{section_name}] PDF for '{title[:45]}' is a scanned circular image. Preserving verified metadata.")
                date_str = f"dated {issue_date}" if issue_date else ""
                fallback_text = (
                    f"Government Engineering College, Ajmer\n"
                    f"Official Circular [{sno}] {date_str}\n"
                    f"College Section: {section_name}\n"
                    f"Title: {title}\n\n"
                    f"Official circular announcement regarding: {title}.\n"
                    f"Published under {section_name} of Government Engineering College, Ajmer.\n"
                    f"Document Reference: {sno}.\n"
                    f"Official circular PDF link: {pdf_url}."
                )
                pages = [{"page_number": 1, "text": fallback_text}]

            full_text = "\n\n".join([p["text"] for p in pages])
            notice_id = f"GECA-{clean_sno}"

            return {
                "id": notice_id,
                "ref_no": sno,
                "title": title,
                "issue_date": issue_date,
                "category": category,
                "section": section_name,
                "department": department_name,
                "content_type": "circular_pdf",
                "summary": full_text[:400].strip() + "..." if len(full_text) > 400 else full_text,
                "full_text": full_text,
                "pdf_path": local_pdf_path,
                "source_url": pdf_url,
                "source_institution": "Government Engineering College, Ajmer",
                "status": f"Active ({section_name} Circular)",
                "page_count": len(pages),
                "chunks_count": 0,
                "_pages": pages
            }
        except Exception as e:
            self.log("ERROR", f"Error parsing PDF at {pdf_url}: {str(e)}")
            return None

    def _scrape_generic_html_portal(self, target_url: str, max_items: int = 8) -> List[Dict[str, Any]]:
        """Fallback 2-level scraper for traditional HTML university portals."""
        self.log("INFO", f"Fetching HTML content from {target_url}...")
        try:
            resp = self.session.get(target_url, timeout=self.timeout, verify=False)
            if resp.status_code != 200:
                self.log("ERROR", f"HTTP {resp.status_code} returned when accessing {target_url}")
                return []
        except Exception as e:
            self.log("ERROR", f"Failed to connect to {target_url}: {str(e)}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        all_links = soup.find_all("a", href=True)
        self.log("INFO", f"Found {len(all_links)} hyperlinks on page.")

        if len(all_links) == 0:
            self.log("WARNING", "The target page contains 0 hyperlinks. It may be rendered via JavaScript. Please use manual PDF upload.")
            return []

        candidates = []
        seen_urls = set()
        for a in all_links:
            href = a["href"].strip()
            if not href or href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
                continue
            full_url = urljoin(target_url, href)
            if full_url in seen_urls:
                continue
            text = a.get_text(" ", strip=True)
            if self.is_pdf_url(full_url) or any(kw in full_url.lower() or kw in text.lower() for kw in self.NOTICE_KEYWORDS):
                seen_urls.add(full_url)
                candidates.append((full_url, text, self.is_pdf_url(full_url)))

        self.log("INFO", f"Filtered down to {len(candidates)} candidate notice & circular links.")
        discovered = []

        for url, desc, is_pdf in candidates:
            if len(discovered) >= max_items:
                break
            title = desc if len(desc) >= 12 else f"Notice Circular: {os.path.basename(urlparse(url).path)}"
            if is_pdf:
                notice = self._process_single_pdf_url(url, title, "University Notice Portal")
                if notice:
                    discovered.append(notice)
                    self.log("SUCCESS", f"Indexed notice: [{notice['ref_no']}] {notice['title']}")

        return discovered

    def _process_single_pdf_url(self, pdf_url: str, title: str, institution: str) -> Optional[Dict[str, Any]]:
        """Downloads a generic PDF and extracts text."""
        try:
            resp = self.session.get(pdf_url, timeout=(3.5, 15.0), verify=False)
            if resp.status_code != 200:
                return None
            filename = os.path.basename(urlparse(pdf_url).path) or "notice.pdf"
            local_path = os.path.join(settings.PDF_DIR, f"GEN_{abs(hash(pdf_url)) % 100000}_{filename}")
            with open(local_path, "wb") as f:
                f.write(resp.content)

            pages = PDFProcessor.extract_text_and_pages(local_path)
            if not pages or not any(p["text"].strip() for p in pages):
                return None

            full_text = "\n\n".join([p["text"] for p in pages])
            notice_id = f"DOC-{abs(hash(pdf_url)) % 100000:05d}"
            return {
                "id": notice_id,
                "ref_no": notice_id,
                "title": title,
                "issue_date": None,
                "category": "General",
                "section": "General College Portal",
                "department": None,
                "content_type": "pdf",
                "summary": full_text[:400] + "...",
                "full_text": full_text,
                "pdf_path": local_path,
                "source_url": pdf_url,
                "source_institution": institution,
                "status": "Active",
                "page_count": len(pages),
                "chunks_count": 0,
                "_pages": pages
            }
        except Exception as e:
            self.log("ERROR", f"Error in generic PDF process: {str(e)}")
            return None
