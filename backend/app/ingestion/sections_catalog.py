"""
Comprehensive catalog of all official sections, cells, departments, and administrative bodies
of Government Engineering College, Ajmer (ecajmer.ac.in).
"""

from typing import Dict, List, Any, Optional

COLLEGE_BASE_URL = "https://www.ecajmer.ac.in"
API_BASE_URL = "https://ecajmer.ac.in/api"

# 1. SPECIAL INSTITUTIONAL SECTIONS
SPECIAL_SECTIONS: List[Dict[str, Any]] = [
    {
        "slug": "principal",
        "name": "Principal & Institutional Administration",
        "category": "Administration",
        "type": "special",
        "endpoint": f"{API_BASE_URL}/principle/principal-public",
        "public_url": f"{COLLEGE_BASE_URL}/administration/PrincipalMessage",
        "description": "Leadership message, institution vision, mission, and administrative directives from Principal Dr. Radha Kishan Motwani."
    },
    {
        "slug": "mandatory-disclosures",
        "name": "Mandatory Disclosures & NBA Accreditation",
        "category": "Administration",
        "type": "special",
        "endpoint": f"{API_BASE_URL}/mandatory-disclosures/get-all",
        "public_url": f"{COLLEGE_BASE_URL}/administration/MandatoryDisclosure",
        "description": "AICTE approvals, NBA accreditation letters, RTI disclosures, and statutory institutional records."
    },
    {
        "slug": "achievements",
        "name": "Student & Institutional Achievements",
        "category": "Student Welfare & Activities",
        "type": "special",
        "endpoint": f"{API_BASE_URL}/public/achievements",
        "public_url": f"{COLLEGE_BASE_URL}/student-corner/achievements",
        "description": "National hackathons, sports trophies, academic honors, and student awards."
    },
    {
        "slug": "academic-calendar",
        "name": "Academic Calendar & Term Schedules",
        "category": "Academics",
        "type": "special",
        "endpoint": f"{API_BASE_URL}/circulars/public/academic-section?page=1&limit=15&mainCategoryId=1",
        "public_url": f"{COLLEGE_BASE_URL}/academics/academic-calendar",
        "description": "BTU/RTU academic calendars, semester commencement dates, winter/summer vacations, and teaching schedules."
    },
    {
        "slug": "tpo-placement",
        "name": "Training and Placement Cell (TPO)",
        "category": "Placement & Industry",
        "type": "special",
        "endpoint": f"{API_BASE_URL}/circulars/public/iii-cell?page=1&limit=15&mainCategoryId=1",
        "public_url": f"{COLLEGE_BASE_URL}/placement/overview",
        "description": "Campus recruitment guidelines, corporate drives, internship circulars, and industry-institute interaction."
    }
]

# 2. OFFICIAL CELLS (36 Cells verified via /api/web/public/cells)
CELL_SECTIONS: List[Dict[str, Any]] = [
    {
        "slug": "examination-section",
        "name": "Examination Section",
        "category": "Examinations",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/examination-section/circulars",
        "description": "BTU/RTU exam forms, admit cards, fee cutoffs, revaluation, copy view orders, and examination timetables."
    },
    {
        "slug": "proctor",
        "name": "Proctor Section & Student Discipline",
        "category": "Proctor & Student Welfare",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/proctor/circulars",
        "description": "Student code of conduct, campus discipline, anti-ragging measures, ID card issuance, and withdrawal/warning orders."
    },
    {
        "slug": "academic-section",
        "name": "Academic Section",
        "category": "Academics",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/academic-section/circulars",
        "description": "BTU enrollment, syllabus notifications, semester promotion rules, registration guidelines, and academic records."
    },
    {
        "slug": "registrar",
        "name": "Registrar Office & Administration",
        "category": "Administration",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/registrar/circulars",
        "description": "Official college orders, gazetted holidays, administrative circulars, service notifications, and general announcements."
    },
    {
        "slug": "accounts",
        "name": "Account Section",
        "category": "Administration",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/accounts/circulars",
        "description": "Tuition fees, college development fees, challan generation, online fee payment portals, and refund rules."
    },
    {
        "slug": "hostels",
        "name": "Hostel Administration & Chief Warden Office",
        "category": "Student Welfare & Hostels",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/hostels/circulars",
        "description": "Hostel room allotment (Boys & Girls AICTE scheme), mess fee schedules, warden contacts, and hostel curfew rules."
    },
    {
        "slug": "scholarship-details",
        "name": "Scholarship & Financial Aid Cell",
        "category": "Student Welfare & Scholarships",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/scholarship-details/circulars",
        "description": "National Scholarship Portal (NSP), Samaj Kalyan scholarships, post-matric schemes, CM Higher Education scholarships."
    },
    {
        "slug": "grievance",
        "name": "Grievance Redressal Cell",
        "category": "Student Welfare & Redressal",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/grievance/circulars",
        "description": "Formal complaint mechanisms, student grievance procedures, committee hearings, and dispute resolution."
    },
    {
        "slug": "studentgrie",
        "name": "Student Grievance Redressal Cell (SGRC)",
        "category": "Student Welfare & Redressal",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/studentgrie/circulars",
        "description": "Statutory AICTE student grievance committee, ombudsman appeals, and confidential grievance lodging."
    },
    {
        "slug": "women-cell",
        "name": "Women Cell & Internal Complaints Committee (ICC)",
        "category": "Student Welfare & Redressal",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/women-cell/circulars",
        "description": "Prevention of sexual harassment (PoSH), female student safety, women empowerment activities, and ICC contacts."
    },
    {
        "slug": "stsc",
        "name": "SC/ST/OBC Cell",
        "category": "Student Welfare & Redressal",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/stsc/circulars",
        "description": "Liaison cell for SC/ST and OBC students, fee exemptions, welfare schemes, and representation."
    },
    {
        "slug": "central-library",
        "name": "Central Library",
        "category": "Academic Facilities",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/central-library/circulars",
        "description": "Book bank distribution circulars, library membership, e-journal subscriptions (IEEE/DELNET), and reading room timings."
    },
    {
        "slug": "first-year",
        "name": "First Year Cell",
        "category": "Academics",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/first-year/circulars",
        "description": "Freshers orientation, student induction program (SIP), Section A-F batches, and first-year academic schedules."
    },
    {
        "slug": "ug-courses",
        "name": "Undergraduate (UG) Courses Cell",
        "category": "Academics",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/ug-courses/circulars",
        "description": "B.Tech credit structure, curriculum schemes, elective allocations, and degree requirements."
    },
    {
        "slug": "pg-courses",
        "name": "Postgraduate (PG) Courses Cell",
        "category": "Academics",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/pg-courses/circulars",
        "description": "M.Tech and MBA course guidelines, seminar schedules, dissertation submissions, and PG promotions."
    },
    {
        "slug": "phd",
        "name": "Research & PhD Cell",
        "category": "Academics & Research",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/phd/circulars",
        "description": "Doctoral research admissions, DRC reviews, synopsis defense, publication guidelines, and BTU research center orders."
    },
    {
        "slug": "aicte",
        "name": "AICTE Cell",
        "category": "Administration",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/aicte/circulars",
        "description": "AICTE extensions of approval (EOA), student fellowship schemes, PRAGATI and SAKSHAM schemes."
    },
    {
        "slug": "iqac",
        "name": "Internal Quality Assurance Cell (IQAC)",
        "category": "Administration",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/iqac/circulars",
        "description": "Institutional quality benchmark, student feedback audits, academic performance indices, and NAAC/NBA metrics."
    },
    {
        "slug": "cas",
        "name": "Career Advancement Scheme (CAS) Cell",
        "category": "Academics",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/cas/circulars",
        "description": "Faculty advancement, academic performance indicators (API), and teaching enhancement."
    },
    {
        "slug": "erp-cell",
        "name": "ERP & IT Portal Cell",
        "category": "Administration",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/erp-cell/circulars",
        "description": "College ERP login, student credentials, digital attendance, and smart campus systems."
    },
    {
        "slug": "iii-cell",
        "name": "Industry Institute Interaction (III) Cell",
        "category": "Placement & Industry",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/iii-cell/circulars",
        "description": "Industrial tours, corporate guest lectures, joint workshops, and industry MoUs."
    },
    {
        "slug": "iic-cell",
        "name": "Institution's Innovation Council (IIC)",
        "category": "Innovation & Research",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/iic-cell/circulars",
        "description": "Ministry of Education (MoE) innovation rankings, hackathons, ideathons, and patent workshops."
    },
    {
        "slug": "startup-cell",
        "name": "Startup & Entrepreneurship Cell",
        "category": "Innovation & Research",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/startup-cell/circulars",
        "description": "Student venture incubation, seed funding schemes, iStart Rajasthan mentorship, and business plan competitions."
    },
    {
        "slug": "alumni-cell",
        "name": "Alumni Association Cell",
        "category": "Campus Life",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/alumni-cell/circulars",
        "description": "Alumni meet, mentorship programs, alumni endowment funds, and graduate network."
    },
    {
        "slug": "ncc",
        "name": "NCC (National Cadet Corps)",
        "category": "Student Welfare & Activities",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/ncc/circulars",
        "description": "Army wing cadet enrollment, Republic Day camp selection, 'B' and 'C' certificate exams."
    },
    {
        "slug": "nss",
        "name": "NSS (National Service Scheme)",
        "category": "Student Welfare & Activities",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/nss/circulars",
        "description": "Blood donation drives, village community camps, plantation drives, and social welfare credits."
    },
    {
        "slug": "sports-department",
        "name": "Sports Department",
        "category": "Student Welfare & Activities",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/sports-department/circulars",
        "description": "Inter-college sports tournaments, annual athletic meet (SPARDHA), cricket, football, volleyball trials."
    },
    {
        "slug": "mhc",
        "name": "Mental Health & Counseling Cell",
        "category": "Student Welfare",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/mhc/circulars",
        "description": "Confidential psychological counseling, exam stress relief workshops, and student wellbeing support."
    },
    {
        "slug": "environment-cell",
        "name": "Environment Cell",
        "category": "Campus Life",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/environment-cell/circulars",
        "description": "Green campus initiatives, solar energy projects, rainwater harvesting, and eco-club drives."
    },
    {
        "slug": "aimlclub",
        "name": "AI & ML Club",
        "category": "Clubs & Activities",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/aimlclub/circulars",
        "description": "Artificial Intelligence & Machine Learning workshops, Kaggle challenges, and deep learning masterclasses."
    },
    {
        "slug": "ececlub",
        "name": "ECE Club (Robotics & IoT)",
        "category": "Clubs & Activities",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/ececlub/circulars",
        "description": "Hardware hackathons, PCB design, drone building, and embedded robotics seminars."
    },
    {
        "slug": "pccclub",
        "name": "PCC Programming Club",
        "category": "Clubs & Activities",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/pccclub/circulars",
        "description": "Competitive programming (CodeChef/LeetCode), algorithms workshops, and internal hackathons."
    },
    {
        "slug": "uba",
        "name": "Unnat Bharat Abhiyan (UBA)",
        "category": "Campus Life",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/uba/circulars",
        "description": "Adoption of rural villages, grassroots technological intervention, and rural development surveys."
    },
    {
        "slug": "value-cell",
        "name": "Human Values & Professional Ethics Cell",
        "category": "Academics",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/value-cell/circulars",
        "description": "Universal Human Values (UHV) foundation workshops, ethics seminars, and character building."
    },
    {
        "slug": "stores",
        "name": "Central Stores & Purchase",
        "category": "Administration",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/stores/circulars",
        "description": "Equipment procurement, lab inventory tenders, and institutional store notices."
    },
    {
        "slug": "nma",
        "name": "National Mission on Applications (NMA) Cell",
        "category": "Innovation & Research",
        "type": "cell",
        "public_url": f"{COLLEGE_BASE_URL}/ui/cells/nma/circulars",
        "description": "Government applied research projects and mission-mode technological development."
    }
]

# 3. OFFICIAL DEPARTMENTS (13 Departments verified via /api/departments/dept/get-dept)
DEPARTMENT_SECTIONS: List[Dict[str, Any]] = [
    {
        "slug": "cs-it",
        "name": "Computer Science & Engineering and IT",
        "short_code": "CSE/IT",
        "category": "Engineering Departments",
        "type": "department",
        "public_url": f"{COLLEGE_BASE_URL}/department/cs-it/about",
        "description": "Department circulars, practical lab timetables, mercy tests, mid-term examinations, and B.Tech projects."
    },
    {
        "slug": "ce",
        "name": "Civil Engineering Department",
        "short_code": "Civil",
        "category": "Engineering Departments",
        "type": "department",
        "public_url": f"{COLLEGE_BASE_URL}/department/ce/about",
        "description": "Civil surveying camps, concrete lab schedules, structural design project notices, and departmental timetables."
    },
    {
        "slug": "me",
        "name": "Mechanical Engineering Department",
        "short_code": "Mechanical",
        "category": "Engineering Departments",
        "type": "department",
        "public_url": f"{COLLEGE_BASE_URL}/department/me/about",
        "description": "Workshop schedules, CAD/CAM lab circulars, thermodynamics practicals, and departmental notifications."
    },
    {
        "slug": "ee",
        "name": "Electrical Engineering Department",
        "short_code": "Electrical",
        "category": "Engineering Departments",
        "type": "department",
        "public_url": f"{COLLEGE_BASE_URL}/department/ee/about",
        "description": "Power systems lab, electrical machines tests, departmental seminar rosters, and mid-term notices."
    },
    {
        "slug": "ece",
        "name": "Electronics & Communication Engineering",
        "short_code": "ECE",
        "category": "Engineering Departments",
        "type": "department",
        "public_url": f"{COLLEGE_BASE_URL}/department/ece/about",
        "description": "VLSI design, digital signal processing labs, microwave lab timetables, and departmental notices."
    },
    {
        "slug": "eic",
        "name": "Electronics Instrumentation & Control",
        "short_code": "EIC",
        "category": "Engineering Departments",
        "type": "department",
        "public_url": f"{COLLEGE_BASE_URL}/department/eic/about",
        "description": "Sensors and transducer labs, process control automation practicals, and departmental circulars."
    },
    {
        "slug": "mca",
        "name": "Master of Computer Applications (MCA)",
        "short_code": "MCA",
        "category": "Postgraduate Departments",
        "type": "department",
        "public_url": f"{COLLEGE_BASE_URL}/department/mca/about",
        "description": "MCA semester schedules, software engineering projects, lab vivas, and departmental notices."
    },
    {
        "slug": "mba",
        "name": "Master of Business Administration (MBA)",
        "short_code": "MBA",
        "category": "Postgraduate Departments",
        "type": "department",
        "public_url": f"{COLLEGE_BASE_URL}/department/mba/about",
        "description": "Management seminars, summer internship project viva, corporate case study schedules, and MBA notices."
    },
    {
        "slug": "physics",
        "name": "Department of Physics",
        "short_code": "Physics",
        "category": "Applied Sciences & Humanities",
        "type": "department",
        "public_url": f"{COLLEGE_BASE_URL}/department/physics/about",
        "description": "Engineering Physics laboratory, optics and modern physics practicals for first-year engineering."
    },
    {
        "slug": "chemistry",
        "name": "Department of Chemistry",
        "short_code": "Chemistry",
        "category": "Applied Sciences & Humanities",
        "type": "department",
        "public_url": f"{COLLEGE_BASE_URL}/department/chemistry/about",
        "description": "Engineering Chemistry lab schedules, water analysis practicals, and environmental science modules."
    },
    {
        "slug": "maths",
        "name": "Department of Mathematics",
        "short_code": "Mathematics",
        "category": "Applied Sciences & Humanities",
        "type": "department",
        "public_url": f"{COLLEGE_BASE_URL}/department/maths/about",
        "description": "Engineering Mathematics (I, II, III, IV), advanced calculus, numerical methods tutorials."
    },
    {
        "slug": "english",
        "name": "Department of English & Humanities",
        "short_code": "English",
        "category": "Applied Sciences & Humanities",
        "type": "department",
        "public_url": f"{COLLEGE_BASE_URL}/department/english/about",
        "description": "Communication skills lab, language lab schedules, soft skills training, and humanities courses."
    },
    {
        "slug": "economy",
        "name": "Department of Economics",
        "short_code": "Economics",
        "category": "Applied Sciences & Humanities",
        "type": "department",
        "public_url": f"{COLLEGE_BASE_URL}/department/economy/about",
        "description": "Engineering economics, financial management, industrial organization, and cost accounting modules."
    }
]

# Combined Complete Catalog
ALL_SECTIONS: List[Dict[str, Any]] = SPECIAL_SECTIONS + CELL_SECTIONS + DEPARTMENT_SECTIONS

# Lookup maps for fast indexing & routing
SECTIONS_BY_SLUG: Dict[str, Dict[str, Any]] = {s["slug"]: s for s in ALL_SECTIONS}

def get_section_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    return SECTIONS_BY_SLUG.get(slug)

def get_sections_by_category(category: str) -> List[Dict[str, Any]]:
    return [s for s in ALL_SECTIONS if s.get("category") == category]

def find_section_by_url(url: str) -> Optional[Dict[str, Any]]:
    clean = url.lower().strip()
    # 1. Exact match against official public URL
    for s in ALL_SECTIONS:
        if s.get("public_url") and s["public_url"].lower() in clean:
            return s

    # 2. Check path segments (prevents false matches like 'ce' inside 'notice')
    from urllib.parse import urlparse
    parsed = urlparse(clean)
    path_segments = [seg.strip() for seg in parsed.path.split("/") if seg.strip()]

    for s in ALL_SECTIONS:
        slug = s["slug"].lower()
        if slug in path_segments:
            return s

    return None
