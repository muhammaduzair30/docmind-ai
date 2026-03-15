from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
import os

from app.db.database import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.core.security import get_current_user
from app.core.logging import logger

router = APIRouter()

class DocumentResponse(BaseModel):
    id: int
    filename: str
    upload_time: datetime
    
    class Config:
        orm_mode = True

@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """List all uploaded documents for the currently authenticated user."""
    docs = db.query(Document).filter(Document.owner_id == user.id).all()
    return docs

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Delete a specific document and its associated chunks."""
    
    doc = db.query(Document).filter(Document.id == document_id, Document.owner_id == user.id).first()
    
    if not doc:
        logger.warning(f"User {user.id} attempted to delete non-existent or unowned document {document_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        
    try:
        # Delete chunks first (manual cascade if DB lacks ON DELETE CASCADE)
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        
        # Delete file from disk
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
            
        # Delete document record
        db.delete(doc)
        db.commit()
        
        logger.info(f"User {user.id} deleted document {document_id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete document {document_id} for user {user.id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete document")
    
    return None
