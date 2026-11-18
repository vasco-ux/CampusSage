from fastapi import APIRouter
from app.config import settings
from app.database.repository import NoticeRepository, DeadlineRepository, ConflictRepository
from app.routers.schemas import SystemHealthResponse

router = APIRouter(prefix="/api", tags=["Health & Status"])

@router.get("/health", response_model=SystemHealthResponse)
def get_health():
    # Attempt to read ChromaDB count if collection initialized
    vector_count = 0
    try:
        from app.rag.vector_store import get_vector_store
        store = get_vector_store()
        vector_count = store.count()
    except Exception:
        vector_count = 0

    return SystemHealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        notice_count=NoticeRepository.count_notices(),
        deadline_count=DeadlineRepository.count_deadlines(),
        conflict_count=ConflictRepository.count_conflicts(),
        vector_store_count=vector_count,
        llm_provider=settings.LLM_PROVIDER,
        embedding_model=settings.EMBEDDING_MODEL
    )
