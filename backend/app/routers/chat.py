from fastapi import APIRouter, HTTPException
from app.routers.schemas import ChatRequest, ChatResponse
from app.rag.vector_store import get_vector_store
from app.rag.generator import CampusRAGGenerator
from app.config import settings

router = APIRouter(prefix="/api/chat", tags=["Student Chatbot"])

@router.post("", response_model=ChatResponse)
def answer_student_question(req: ChatRequest):
    """
    RAG-powered student inquiry endpoint.
    Retrieves semantic passages from ChromaDB and grounds LLM responses with citations.
    Supports conversational memory and greetings.
    """
    query = req.question.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Handle conversational greetings immediately without vector lookup
    if CampusRAGGenerator.is_conversational_greeting(query):
        return ChatResponse(**CampusRAGGenerator.get_greeting_response(query))

    # 2. Contextualize query with recent history for follow-up questions
    retrieval_query = query
    if req.history and len(req.history) > 0:
        # Check if query is short or looks like a follow up
        lower_q = query.lower()
        if len(query.split()) <= 4 or any(w in lower_q for w in ["it", "this", "that", "fee", "date", "when", "how much", "reval"]):
            last_user_turn = ""
            for turn in reversed(req.history):
                if turn.get("role") == "user":
                    last_user_turn = turn.get("content", "")
                    break
            if last_user_turn and last_user_turn != query:
                retrieval_query = f"{last_user_turn} {query}"

    # 3. Retrieve top-k semantic chunks from ChromaDB with optional section/category filtering
    vector_store = get_vector_store()
    retrieved_chunks = vector_store.similarity_search(
        retrieval_query,
        top_k=settings.SIMILARITY_TOP_K,
        category=req.category,
        section=req.section
    )

    # 4. Generate grounded answer with citations and history
    response_data = CampusRAGGenerator.generate_answer(query, retrieved_chunks, req.history)

    return ChatResponse(**response_data)
