from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, description="The question to ask the AI. Must be at least 3 characters.")


class QueryResponse(BaseModel):
    answer: str