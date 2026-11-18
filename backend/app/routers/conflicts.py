from fastapi import APIRouter
from typing import List, Dict, Any
from app.database.repository import ConflictRepository

router = APIRouter(prefix="/api/conflicts", tags=["Notice Conflicts & Updates"])

@router.get("", response_model=List[Dict[str, Any]])
def list_conflicts():
    """Retrieve all flagged notice discrepancies and date postponements."""
    return ConflictRepository.get_all_conflicts()
