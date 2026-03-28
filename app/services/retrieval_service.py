from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional

from app.services.embedding_service import generate_embeddings
from app.core.logging import logger

def retrieve_chunks(
    db: Session,
    question: str,
    user_id: int,
    document_id: Optional[int] = None,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve document chunks using Hybrid Search (Reciprocal Rank Fusion)
    merging FTS (Keyword) and pgvector (Semantic) rankings.
    """

    logger.info(f"Retrieving chunks for user {user_id} and question: '{question}' using Hybrid Search")
    query_embedding = generate_embeddings([question])[0]
    limit = top_k * 4 # Fetch extra for rank fusion

    # Add optional document_id to filters
    vector_where = "d.owner_id = :user_id"
    keyword_where = "d.owner_id = :user_id AND dc.fts_tokens @@ plainto_tsquery('english', :question)"
    
    params = {
        "user_id": user_id,
        "embedding": str(query_embedding),
        "question": question,
        "limit": limit
    }

    if document_id is not None:
        vector_where += " AND d.id = :document_id"
        keyword_where += " AND d.id = :document_id"
        params["document_id"] = document_id

    # 1. Semantic Search (pgvector)
    vector_sql = text(f"""
        SELECT dc.id, dc.chunk_text,
               ROW_NUMBER() OVER (ORDER BY dc.embedding <-> :embedding) as rank,
               d.id as doc_id, d.filename as doc_name
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE {vector_where}
        LIMIT :limit
    """)
    vector_results = db.execute(vector_sql, params).fetchall()

    # 2. Keyword Search (PostgreSQL FTS)
    keyword_sql = text(f"""
        SELECT dc.id, dc.chunk_text,
               ROW_NUMBER() OVER (ORDER BY ts_rank_cd(dc.fts_tokens, plainto_tsquery('english', :question)) DESC) as rank,
               d.id as doc_id, d.filename as doc_name
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE {keyword_where}
        LIMIT :limit
    """)
    keyword_results = db.execute(keyword_sql, params).fetchall()

    # 3. Reciprocal Rank Fusion (RRF)
    k = 60
    scores = {}
    chunk_data = {}

    for row in vector_results:
        chunk_id, text_content, rank, doc_id, doc_name = row
        scores[chunk_id] = 1.0 / (k + rank)
        chunk_data[chunk_id] = {
            "document_id": doc_id,
            "document_name": doc_name,
            "chunk_text": text_content
        }

    for row in keyword_results:
        chunk_id, text_content, rank, doc_id, doc_name = row
        if chunk_id not in scores:
            scores[chunk_id] = 0.0
            chunk_data[chunk_id] = {
                "document_id": doc_id,
                "document_name": doc_name,
                "chunk_text": text_content
            }
        scores[chunk_id] += 1.0 / (k + rank)

    # Sort chunks by RRF score descending
    sorted_chunks = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_chunks = [chunk_data[chunk_id] for chunk_id, score in sorted_chunks[:top_k]]

    # Fallback if no text matched strictly but semantic worked
    if not top_chunks and vector_results:
        top_chunks = [{
            "document_id": row[3],
            "document_name": row[4],
            "chunk_text": row[1]
        } for row in vector_results[:top_k]]

    logger.info(f"Retrieved {len(top_chunks)} chunks for user {user_id} via Hybrid Search")
    return top_chunks