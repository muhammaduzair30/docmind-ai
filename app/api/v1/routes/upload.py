import os
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.user import User
from app.db.database import get_db
from app.utils.file_loader import load_document
from app.services.embedding_service import process_document
from app.core.security import get_current_user
from app.core.logging import logger

router = APIRouter()

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def process_document_bg(file_path: str, document_id: int):
    """Background task to extract text and generate embeddings."""
    try:
        # We need a new session for the background task
        from app.db.database import SessionLocal
        db = SessionLocal()
        
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            
            # Extract filename from path
            filename = os.path.basename(file_path)
            text = load_document(file_bytes, filename)
            
            logger.info(f"Background processing started for document {document_id}")
            process_document(db, document_id, text)
            logger.info(f"Background processing completed for document {document_id}")
            
        except Exception as e:
            logger.exception(f"Error processing document {document_id}")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.exception("Failed to start background task")


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    
    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"User {user.id} attempted to upload unsupported file type: {ext}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
        
    try:
        file_path = os.path.join(UPLOAD_DIR, f"{user.id}_{file.filename}")

        with open(file_path, "wb") as buffer:
            file_bytes = file.file.read()
            # Simple size validation (e.g., max 10MB)
            if len(file_bytes) > 10 * 1024 * 1024:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 10MB)")
            buffer.write(file_bytes)

        # Create DB record
        doc = Document(
            filename=file.filename,
            file_path=file_path,
            owner_id=user.id
        )

        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        logger.info(f"User {user.id} uploaded document {doc.id} ({file.filename})")

        # Offload text extraction and embedding to background task
        background_tasks.add_task(process_document_bg, file_path=file_path, document_id=doc.id)

        return {
            "document_id": doc.id,
            "filename": file.filename,
            "message": "Document uploaded successfully. Processing started in the background."
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception(f"Upload failed for user {user.id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during upload")