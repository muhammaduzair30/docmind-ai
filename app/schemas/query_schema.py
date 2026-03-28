from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, description="The question to ask the AI. Must be at least 3 characters.")
    document_id: Optional[int] = Field(default=None, description="Optional document ID. If provided, the AI will answer using only this document.")


class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source chunks used.")