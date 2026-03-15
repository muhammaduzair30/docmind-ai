from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from typing import List

from app.rag.chunker import chunk_text
from app.models.document_chunk import DocumentChunk

# Load model once when server starts
model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of text chunks.
    """

    embeddings = model.encode(texts)

    return [embedding.tolist() for embedding in embeddings]


def process_document(db: Session, document_id: int, text: str):
    """
    Chunk text, generate embeddings, and store DocumentChunk records in the DB.
    """

    chunks: List[str] = chunk_text(text)

    embeddings = generate_embeddings(chunks)

    for chunk, embedding in zip(chunks, embeddings):

        db_chunk = DocumentChunk(
            document_id=document_id,
            chunk_text=chunk,
            embedding=embedding
        )

        db.add(db_chunk)

    db.commit()
    
    # Generate PostgreSQL TSVECTOR for Full-Text Search
    from sqlalchemy import text
    db.execute(
        text("UPDATE document_chunks SET fts_tokens = to_tsvector('english', chunk_text) WHERE document_id = :doc_id"),
        {"doc_id": document_id}
    )
    db.commit()

    return {
        "chunks": len(chunks),
        "message": f"Processed {len(chunks)} chunks for document {document_id}"
    }