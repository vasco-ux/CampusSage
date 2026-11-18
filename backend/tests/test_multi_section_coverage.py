import pytest
from app.database.connection import init_db
from app.database.repository import NoticeRepository, DeadlineRepository
from app.rag.vector_store import get_vector_store
from app.ingestion.sections_catalog import ALL_SECTIONS, get_section_by_slug
from app.routers.ingest import get_college_sections
from app.routers.notices import list_notices, get_notice_filters
from app.routers.chat import answer_student_question
from app.routers.schemas import ChatRequest

@pytest.fixture(scope="module", autouse=True)
def setup_multi_section_data():
    init_db()
    test_notices = [
        {
            "id": "SEC-TEST-PROC-01",
            "ref_no": "PROCT/2026/01",
            "title": "Proctor Office Student Discipline and Anti-Ragging Guidelines",
            "issue_date": "2026-10-15",
            "category": "Proctor & Student Welfare",
            "section": "Proctor Section & Student Discipline",
            "department": None,
            "content_type": "webpage",
            "summary": "Strict compliance with UGC anti-ragging regulations. Disciplinary action for misconduct on campus.",
            "full_text": "Strict compliance with UGC anti-ragging regulations. Disciplinary action for misconduct on campus. Chief Proctor contact details.",
            "pdf_path": None,
            "source_url": "https://www.ecajmer.ac.in/ui/cells/proctor/circulars",
            "source_institution": "Government Engineering College, Ajmer",
            "status": "Active (Proctor Section)",
            "chunks_count": 1
        },
        {
            "id": "SEC-TEST-CSE-02",
            "ref_no": "CSE/2026/44",
            "title": "Mercy Test and Practical Examination for B.Tech V Semester CSE",
            "issue_date": "2026-10-20",
            "category": "Engineering Departments",
            "section": "Computer Science & Engineering and IT",
            "department": "Computer Science & Engineering and IT",
            "content_type": "circular_pdf",
            "summary": "Mercy test scheduled on 28.10.2026 for students who missed Mid-Term practicals.",
            "full_text": "Mercy test scheduled on 28.10.2026 for students who missed Mid-Term practicals in Computer Science laboratories.",
            "pdf_path": None,
            "source_url": "https://www.ecajmer.ac.in/department/cs-it/about",
            "source_institution": "Government Engineering College, Ajmer",
            "status": "Active (CSE Circular)",
            "chunks_count": 1
        }
    ]

    for n in test_notices:
        NoticeRepository.insert_notice(n)

    vstore = get_vector_store()
    vstore.add_chunks([
        {
            "id": "chunk_proctor_test",
            "text": "Strict compliance with UGC anti-ragging regulations. Disciplinary action for misconduct on campus. Chief Proctor contact details.",
            "metadata": {
                "notice_id": "SEC-TEST-PROC-01",
                "ref_no": "PROCT/2026/01",
                "title": "Proctor Office Student Discipline and Anti-Ragging Guidelines",
                "category": "Proctor & Student Welfare",
                "section": "Proctor Section & Student Discipline",
                "department": "",
                "content_type": "webpage",
                "page": 1,
                "source_url": "https://www.ecajmer.ac.in/ui/cells/proctor/circulars"
            }
        },
        {
            "id": "chunk_cse_test",
            "text": "Mercy test scheduled on 28.10.2026 for students who missed Mid-Term practicals in Computer Science laboratories.",
            "metadata": {
                "notice_id": "SEC-TEST-CSE-02",
                "ref_no": "CSE/2026/44",
                "title": "Mercy Test and Practical Examination for B.Tech V Semester CSE",
                "category": "Engineering Departments",
                "section": "Computer Science & Engineering and IT",
                "department": "Computer Science & Engineering and IT",
                "content_type": "circular_pdf",
                "page": 1,
                "source_url": "https://www.ecajmer.ac.in/department/cs-it/about"
            }
        }
    ])

def test_sections_catalog_service():
    result = get_college_sections()
    assert "sections" in result
    sections = result["sections"]
    assert len(sections) >= 50
    slugs = [s["slug"] for s in sections]
    assert "examination-section" in slugs
    assert "proctor" in slugs
    assert "hostels" in slugs
    assert "cs-it" in slugs
    assert "principal" in slugs
    assert "central-library" in slugs

def test_notices_section_and_department_filtering():
    # Filter by Proctor section
    proc_items = list_notices(section="Proctor Section & Student Discipline")
    assert len(proc_items) >= 1
    assert all("Proctor" in item["section"] for item in proc_items)

    # Filter by CSE department
    cse_items = list_notices(department="Computer Science & Engineering and IT")
    assert len(cse_items) >= 1
    assert all("Computer Science" in item["section"] for item in cse_items)

    # Filter metadata service
    filters = get_notice_filters()
    assert "sections" in filters
    assert len(filters["sections"]) >= 2
    assert "stats" in filters

def test_chat_multi_section_inquiry_and_citations():
    # Scoped question for Proctor office
    req = ChatRequest(
        question="What are the anti-ragging regulations and student discipline guidelines?",
        section="Proctor Section & Student Discipline"
    )
    res = answer_student_question(req)
    assert res.grounded is True
    assert len(res.sources) >= 1
    top_src = res.sources[0]
    assert "Proctor" in (top_src.section or "") or "PROCT" in top_src.id
    assert "UGC anti-ragging" in res.answer or "discipline" in res.answer.lower()
