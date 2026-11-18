from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional
from app.database.repository import DeadlineRepository

router = APIRouter(prefix="/api/deadlines", tags=["Academic Deadlines"])

@router.get("", response_model=List[Dict[str, Any]])
def list_deadlines(
    category: Optional[str] = Query(None, description="Filter by category"),
    section: Optional[str] = Query(None, description="Filter by section"),
    department: Optional[str] = Query(None, description="Filter by department"),
    search: Optional[str] = Query(None, description="Search in title or source")
):
    """Retrieve all upcoming academic deadlines ordered chronologically with optional filters."""
    cat_val = category if isinstance(category, str) else None
    sec_val = section if isinstance(section, str) else None
    dept_val = department if isinstance(department, str) else None
    search_val = search if isinstance(search, str) else None

    return DeadlineRepository.get_all_deadlines(
        category=cat_val,
        section=sec_val,
        department=dept_val,
        search=search_val
    )
