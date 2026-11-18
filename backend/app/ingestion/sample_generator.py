import os
import fitz  # PyMuPDF
from typing import List, Dict, Any
from app.config import settings
from app.database.repository import NoticeRepository, DeadlineRepository, ConflictRepository

SAMPLE_NOTICES = [
    {
        "id": "NOT-2026-089",
        "ref_no": "COE/EXAM/2026/89",
        "title": "Revised Schedule for 7th Semester B.Tech End-Semester Examination",
        "issue_date": "2026-10-28",
        "category": "Examinations",
        "summary": "End-semester examinations originally starting Nov 15 are postponed to Nov 22, 2026 due to university youth festival. Form submission deadline extended.",
        "full_text": """OFFICE OF THE CONTROLLER OF EXAMINATIONS
COLLEGE OF ENGINEERING & TECHNOLOGY
Ref. No: COE/EXAM/2026/89                                Date: October 28, 2026

CIRCULAR: REVISED END-SEMESTER EXAMINATION SCHEDULE

In partial modification of earlier notification Ref. No: COE/EXAM/2026/72 dated October 10, 2026, all Seventh Semester B.Tech students are hereby informed that the commencement of the Odd Semester End-Semester Examinations has been rescheduled.

Due to the upcoming State University Inter-College Youth Festival hosted on campus from November 14 to November 18, 2026, the examination schedule is revised as follows:

1. Revised Examination Commencement Date: November 22, 2026 (Sunday).
2. The examination timings shall remain 09:30 AM to 12:30 PM.
3. The last date to submit online examination forms without late fine has been extended to November 05, 2026.
4. Examination forms submitted with a late fee of Rs. 500 will be accepted up to November 08, 2026.
5. Admit cards will be available for download from the ERP portal starting November 18, 2026.

All students must note that possession of physical admit cards and college identity cards is strictly mandatory.

By order of Controller of Examinations.""",
        "status": "Active (Revision)",
        "supersedes": "NOT-2026-072"
    },
    {
        "id": "NOT-2026-072",
        "ref_no": "COE/EXAM/2026/72",
        "title": "Schedule and Form Submission for 7th & 8th Semester Examinations",
        "issue_date": "2026-10-10",
        "category": "Examinations",
        "summary": "Examination form submission deadline is Nov 01, 2026. Exams scheduled to begin Nov 15, 2026 [SUPERSEDED].",
        "full_text": """OFFICE OF THE CONTROLLER OF EXAMINATIONS
Ref. No: COE/EXAM/2026/72                                Date: October 10, 2026

NOTICE: REGISTRATION AND COMMENCEMENT OF ODD SEMESTER EXAMINATIONS 2026

All registered candidates for B.Tech Semester VII and VIII examinations are notified that the form submission window is active.

Key dates:
- Online form filling commencement: October 15, 2026.
- Last date to submit forms without fine: November 01, 2026.
- Examination commencement date: November 15, 2026.

Students having outstanding fee dues must clear accounts before form verification.
Sd/-
Controller of Examinations.""",
        "status": "Superseded",
        "superseded_by": "NOT-2026-089"
    },
    {
        "id": "NOT-2026-084",
        "ref_no": "ACAD/FEE/2026/84",
        "title": "Mandatory Academic Fee Clearance for Odd Semester 2026-27",
        "issue_date": "2026-10-22",
        "category": "Fees",
        "summary": "All undergraduate students must clear tuition dues by Nov 10, 2026. Late fine of Rs. 100/day applies thereafter up to Nov 17, 2026.",
        "full_text": """OFFICE OF THE DEAN ACADEMIC AFFAIRS
Ref. No: ACAD/FEE/2026/84                                Date: October 22, 2026

URGENT NOTICE: TUITION FEE CLEARANCE & DUES PAYMENT

All undergraduate (B.Tech) students of 2nd, 3rd, and 4th years are hereby directed to clear their pending tuition fees and laboratory charges for Odd Semester 2026-27.

1. Deadline for payment without late fine: November 10, 2026 (5:00 PM).
2. Late fee policy: A fine of Rs. 100 per calendar day will be levied from November 11 to November 17, 2026.
3. Mode of payment: Online via Net Banking / UPI on the SBI Collect College Portal only. Cash payments are strictly prohibited.
4. Consequences of non-payment: Students failing to pay by November 17, 2026 will not be issued examination admit cards and will be debarred from mid-term assessments.

For queries or fee receipts, contact the Accounts Section at Room 104, Admin Block.
Dean (Academic Affairs)""",
        "status": "Active"
    },
    {
        "id": "NOT-2026-092",
        "ref_no": "TPO/DRIVE/2026/92",
        "title": "TCS & Infosys Campus Placement Drive Guidelines",
        "issue_date": "2026-11-01",
        "category": "Placements",
        "summary": "Final year B.Tech students with CGPA >= 6.5 and no active backlogs must register before Nov 12, 2026, 5:00 PM.",
        "full_text": """TRAINING AND PLACEMENT CELL
Ref. No: TPO/DRIVE/2026/92                                Date: November 01, 2026

CIRCULAR: UPCOMING RECRUITMENT DRIVES - TCS (NINJA/DIGITAL) & INFOSYS (SP/DSE)

We are pleased to announce the joint recruitment process for 2027 graduating batch.

Eligibility Criteria:
- Program: B.Tech (CSE, IT, ECE, EE, ME).
- Academic Record: Minimum 65% or 6.5 CGPA in 10th, 12th, and all completed semesters.
- Backlogs: No active backlogs allowed at the time of online aptitude assessment.

Registration Timeline:
- Registration Portal opens: November 02, 2026.
- Final Registration Deadline: November 12, 2026 at 5:00 PM sharp.
- Online Aptitude & Coding Round: November 19, 2026.

Interested and eligible candidates must fill out the Google Form circulated on official college email and upload updated resumes.
Training & Placement Officer""",
        "status": "Active"
    },
    {
        "id": "NOT-2026-065",
        "ref_no": "CSE/CONF/2026/65",
        "title": "National Conference on AI and Quantum Computing (NCAIQC-2026)",
        "issue_date": "2026-09-30",
        "category": "Academics",
        "summary": "Call for student research papers. Submission deadline Nov 20, 2026. Selected papers published in indexed proceedings.",
        "full_text": """DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING
Ref. No: CSE/CONF/2026/65                                Date: September 30, 2026

CALL FOR PAPERS: 3RD NATIONAL CONFERENCE ON AI & QUANTUM COMPUTING

The Department of Computer Science & Engineering invites original research contributions from students, research scholars, and faculty members for NCAIQC-2026.

Important Deadlines:
- Full Paper Submission: November 20, 2026.
- Notification of Acceptance: November 28, 2026.
- Camera-Ready Paper & Registration: December 05, 2026.
- Conference Dates: December 18-19, 2026.

Tracks include Machine Learning, Large Language Models, Retrieval-Augmented Generation, and Quantum Information Theory.
All accepted and presented papers will be indexed in standard IEEE/Scopus proceedings.

Prof. & Head, Department of CSE""",
        "status": "Active"
    }
]

SAMPLE_DEADLINES = [
    {
        "id": "DL-1",
        "title": "Examination Form Submission (Without Fine)",
        "deadline_date": "2026-11-05",
        "category": "Examinations",
        "urgency": "urgent",
        "source_notice_id": "NOT-2026-089",
        "source_title": "Revised Schedule for 7th Semester B.Tech End-Semester Examination",
        "notes": "Extended from Nov 01 as per revised circular COE/EXAM/2026/89.",
        "is_active": 1
    },
    {
        "id": "DL-2",
        "title": "Tuition Fee Clearance (Odd Semester)",
        "deadline_date": "2026-11-10",
        "category": "Fees",
        "urgency": "approaching",
        "source_notice_id": "NOT-2026-084",
        "source_title": "Mandatory Academic Fee Clearance for Odd Semester 2026-27",
        "notes": "Rs. 100/day late fine levied thereafter up to Nov 17.",
        "is_active": 1
    },
    {
        "id": "DL-3",
        "title": "Placement Drive Registration (TCS & Infosys)",
        "deadline_date": "2026-11-12",
        "category": "Placements",
        "urgency": "approaching",
        "source_notice_id": "NOT-2026-092",
        "source_title": "TCS & Infosys Campus Placement Drive Guidelines",
        "notes": "Closes at 5:00 PM. Minimum CGPA 6.5, no active backlogs.",
        "is_active": 1
    },
    {
        "id": "DL-4",
        "title": "7th Semester End-Semester Exams Commencement",
        "deadline_date": "2026-11-22",
        "category": "Examinations",
        "urgency": "upcoming",
        "source_notice_id": "NOT-2026-089",
        "source_title": "Revised Schedule for 7th Semester B.Tech End-Semester Examination",
        "notes": "Postponed from Nov 15 due to University Youth Festival.",
        "is_active": 1
    },
    {
        "id": "DL-5",
        "title": "Paper Submission: National Conference on AI (NCAIQC-2026)",
        "deadline_date": "2026-11-20",
        "category": "Academics",
        "urgency": "upcoming",
        "source_notice_id": "NOT-2026-065",
        "source_title": "National Conference on AI and Quantum Computing (NCAIQC-2026)",
        "notes": "Full paper submission deadline for student researchers.",
        "is_active": 1
    }
]

SAMPLE_CONFLICTS = [
    {
        "id": "CONF-1",
        "topic": "7th Semester B.Tech Exam Commencement Date",
        "severity": "high",
        "original_notice_id": "NOT-2026-072",
        "superseding_notice_id": "NOT-2026-089",
        "original_date": "2026-11-15",
        "revised_date": "2026-11-22",
        "resolution": "Active deadline updated to November 22, 2026. The older notice is flagged as superseded."
    }
]

def generate_pdf_for_notice(notice: Dict[str, Any]) -> str:
    """Generates a genuine college notice PDF using PyMuPDF and saves to raw_pdfs."""
    pdf_filename = f"{notice['id']}.pdf"
    pdf_path = os.path.join(settings.PDF_DIR, pdf_filename)
    
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # Standard A4
    
    # Title / Header
    header_text = f"OFFICIAL CIRCULAR: {notice['ref_no']}\n{notice['title'].upper()}"
    page.insert_text(fitz.Point(50, 60), header_text, fontsize=12, fontname="helv", color=(0.1, 0.2, 0.4))
    
    # Body text
    body = notice['full_text']
    page.insert_textbox(fitz.Rect(50, 110, 545, 780), body, fontsize=10, fontname="helv")
    
    doc.save(pdf_path)
    doc.close()
    return pdf_path

def seed_sample_data():
    """Generates official sample PDFs and populates SQLite database tables."""
    print("[SAMPLE SEEDER] Generating sample notices and PDFs...")
    
    for notice in SAMPLE_NOTICES:
        pdf_path = generate_pdf_for_notice(notice)
        notice_data = notice.copy()
        notice_data["pdf_path"] = pdf_path
        notice_data["source_url"] = f"https://college.edu.in/notices/{notice['id']}"
        notice_data["chunks_count"] = 4
        NoticeRepository.insert_notice(notice_data)

    for dl in SAMPLE_DEADLINES:
        DeadlineRepository.insert_deadline(dl)

    for conf in SAMPLE_CONFLICTS:
        ConflictRepository.insert_conflict(conf)

    print(f"[SAMPLE SEEDER] Seeded {len(SAMPLE_NOTICES)} notices, {len(SAMPLE_DEADLINES)} deadlines, and {len(SAMPLE_CONFLICTS)} conflicts.")
