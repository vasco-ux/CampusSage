from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    question: str = Field(..., description="Student's natural language question")
    history: Optional[List[Dict[str, str]]] = Field(default=[], description="Previous conversation turns")
    section: Optional[str] = Field(default=None, description="Optional college section filter")
    category: Optional[str] = Field(default=None, description="Optional category filter")

class SourceCitation(BaseModel):
    id: str
    title: str
    date: Optional[str] = None
    page: int = 1
    snippet: str
    category: Optional[str] = None
    section: Optional[str] = None
    department: Optional[str] = None
    content_type: Optional[str] = "circular_pdf"
    similarity: Optional[str] = "High"
    source_url: Optional[str] = None
    pdf_url: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    grounded: bool = True
    confidence: str = "High"
    conflict_alert: Optional[str] = None
    sources: List[SourceCitation] = []

class IngestRequest(BaseModel):
    url: Optional[str] = Field(default=None, description="Target college notice board URL")
    section_slug: Optional[str] = Field(default=None, description="Optional specific section slug")
    max_items: Optional[int] = Field(default=5, description="Maximum circulars/documents to ingest per section")

class SystemHealthResponse(BaseModel):
    status: str
    app_name: str
    notice_count: int
    deadline_count: int
    conflict_count: int
    vector_store_count: int
    llm_provider: str
    embedding_model: str
