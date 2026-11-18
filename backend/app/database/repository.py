from typing import List, Optional, Dict, Any
from app.database.connection import get_db

class NoticeRepository:
    @staticmethod
    def insert_notice(notice: Dict[str, Any]):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO notices (
                id, ref_no, title, issue_date, category, summary, full_text,
                pdf_path, source_url, source_institution, status, superseded_by, chunks_count,
                section, department, content_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                notice.get("id"),
                notice.get("ref_no"),
                notice.get("title"),
                notice.get("issue_date"),
                notice.get("category"),
                notice.get("summary"),
                notice.get("full_text"),
                notice.get("pdf_path"),
                notice.get("source_url"),
                notice.get("source_institution", "Government Engineering College, Ajmer"),
                notice.get("status", "Active"),
                notice.get("superseded_by"),
                notice.get("chunks_count", 0),
                notice.get("section"),
                notice.get("department"),
                notice.get("content_type", "pdf")
            ))

    @staticmethod
    def get_all_notices(
        category: Optional[str] = None,
        search: Optional[str] = None,
        source: Optional[str] = None,
        section: Optional[str] = None,
        department: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM notices WHERE 1=1"
            params = []
            
            if category and category != "All":
                query += " AND category = ?"
                params.append(category)

            if section and section != "All":
                query += " AND section = ?"
                params.append(section)

            if department and department != "All":
                query += " AND department = ?"
                params.append(department)

            if source and source != "All":
                if source == "GEC Ajmer":
                    query += " AND (source_institution LIKE '%Ajmer%' OR source_url LIKE '%ecajmer%')"
                elif source == "User Upload":
                    query += " AND (source_institution LIKE '%Upload%' OR source_url LIKE 'local://upload%')"
                else:
                    query += " AND source_institution = ?"
                    params.append(source)
            
            if search:
                query += " AND (title LIKE ? OR summary LIKE ? OR ref_no LIKE ? OR section LIKE ?)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param, search_param])
                
            query += " ORDER BY issue_date DESC, created_at DESC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_notice_by_id(notice_id: str) -> Optional[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notices WHERE id = ?", (notice_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def count_notices() -> int:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM notices")
            return cursor.fetchone()[0]

    @staticmethod
    def get_distinct_sections() -> List[str]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT section FROM notices WHERE section IS NOT NULL AND section != '' ORDER BY section")
            return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def get_distinct_departments() -> List[str]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT department FROM notices WHERE department IS NOT NULL AND department != '' ORDER BY department")
            return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def get_section_stats() -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 
                COALESCE(section, 'General / Other') as section_name,
                COUNT(*) as doc_count,
                SUM(chunks_count) as total_chunks,
                MAX(created_at) as last_indexed
            FROM notices 
            GROUP BY section
            ORDER BY doc_count DESC
            """)
            return [dict(row) for row in cursor.fetchall()]


class DeadlineRepository:
    @staticmethod
    def insert_deadline(dl: Dict[str, Any]):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO deadlines (
                id, title, deadline_date, category, urgency,
                source_notice_id, source_title, source_url, pdf_path, notes, is_active,
                section, department
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dl.get("id"),
                dl.get("title"),
                dl.get("deadline_date"),
                dl.get("category", "General"),
                dl.get("urgency", "upcoming"),
                dl.get("source_notice_id"),
                dl.get("source_title"),
                dl.get("source_url"),
                dl.get("pdf_path"),
                dl.get("notes"),
                dl.get("is_active", 1),
                dl.get("section"),
                dl.get("department")
            ))

    @staticmethod
    def get_all_deadlines(
        category: Optional[str] = None,
        section: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 60
    ) -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM deadlines WHERE is_active = 1"
            params = []
            
            if category and category != "All":
                query += " AND category = ?"
                params.append(category)

            if section and section != "All":
                query += " AND section = ?"
                params.append(section)

            if department and department != "All":
                query += " AND department = ?"
                params.append(department)

            if search:
                query += " AND (title LIKE ? OR source_title LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])

            query += " ORDER BY deadline_date ASC LIMIT ?"
            params.append(limit)
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def count_deadlines() -> int:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM deadlines WHERE is_active = 1")
            return cursor.fetchone()[0]


class ConflictRepository:
    @staticmethod
    def insert_conflict(conflict: Dict[str, Any]):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO conflicts (
                id, topic, severity, original_notice_id, superseding_notice_id,
                original_date, revised_date, resolution
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conflict.get("id"),
                conflict.get("topic"),
                conflict.get("severity", "medium"),
                conflict.get("original_notice_id"),
                conflict.get("superseding_notice_id"),
                conflict.get("original_date"),
                conflict.get("revised_date"),
                conflict.get("resolution")
            ))

    @staticmethod
    def get_all_conflicts() -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(conflicts);")
            cols = [row["name"] for row in cursor.fetchall()]
            order_col = "created_at" if "created_at" in cols else ("detected_at" if "detected_at" in cols else "id")
            cursor.execute(f"SELECT * FROM conflicts ORDER BY {order_col} DESC")
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def count_conflicts() -> int:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM conflicts")
            return cursor.fetchone()[0]
