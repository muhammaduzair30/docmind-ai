from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.query_schema import QueryRequest, QueryResponse
from app.services.rag_service import ask_question
from app.models.user import User
from app.core.security import get_current_user
from app.core.logging import logger
from app.core.rate_limiter import limiter

router = APIRouter()


@router.post("/", response_model=QueryResponse)
@limiter.limit("15/minute")
def ask(
    request: Request,
    query_req: QueryRequest, 
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    try:
        # Handled cleanly inside arg validation, but good practice
        if not query_req.question or len(query_req.question.strip()) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question cannot be empty")
            
        logger.info(f"User {user.id} asked query: '{query_req.question}' (doc_id: {query_req.document_id})")
        answer, sources = ask_question(
            db=db, 
            question=query_req.question, 
            user_id=user.id,
            document_id=query_req.document_id
        )
        
        return {"answer": answer, "sources": sources}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception(f"Query failed for user {user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An error occurred while answering your question."
        )