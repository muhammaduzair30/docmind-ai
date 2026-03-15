from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

from app.services.embedding_service import generate_embeddings
from app.core.logging import logger

def retrieve_chunks(
    db: Session,
    question: str,
    user_id: int,
    top_k: int = 5
) -> List[str]:
    """
    Retrieve document chunks using Hybrid Search (Reciprocal Rank Fusion)
    merging FTS (Keyword) and pgvector (Semantic) rankings.
    """

    logger.info(f"Retrieving chunks for user {user_id} and question: '{question}' using Hybrid Search")
    query_embedding = generate_embeddings([question])[0]
    limit = top_k * 4 # Fetch extra for rank fusion

    # 1. Semantic Search (pgvector)
    vector_sql = text("""
        SELECT dc.id, dc.chunk_text,
               ROW_NUMBER() OVER (ORDER BY dc.embedding <-> :embedding) as rank
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE d.owner_id = :user_id
        LIMIT :limit
    """)
    vector_results = db.execute(vector_sql, {"user_id": user_id, "embedding": str(query_embedding), "limit": limit}).fetchall()

    # 2. Keyword Search (PostgreSQL FTS)
    keyword_sql = text("""
        SELECT dc.id, dc.chunk_text,
               ROW_NUMBER() OVER (ORDER BY ts_rank_cd(dc.fts_tokens, plainto_tsquery('english', :question)) DESC) as rank
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE d.owner_id = :user_id AND dc.fts_tokens @@ plainto_tsquery('english', :question)
        LIMIT :limit
    """)
    keyword_results = db.execute(keyword_sql, {"user_id": user_id, "question": question, "limit": limit}).fetchall()

    # 3. Reciprocal Rank Fusion (RRF)
    k = 60
    scores = {}
    chunk_texts = {}

    for row in vector_results:
        chunk_id, text_content, rank = row
        scores[chunk_id] = 1.0 / (k + rank)
        chunk_texts[chunk_id] = text_content

    for row in keyword_results:
        chunk_id, text_content, rank = row
        if chunk_id not in scores:
            scores[chunk_id] = 0.0
            chunk_texts[chunk_id] = text_content
        scores[chunk_id] += 1.0 / (k + rank)

    # Sort chunks by RRF score descending
    sorted_chunks = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_chunk_texts = [chunk_texts[chunk_id] for chunk_id, score in sorted_chunks[:top_k]]

    # Fallback if no text matched strictly but semantic worked
    if not top_chunk_texts and vector_results:
        top_chunk_texts = [row[1] for row in vector_results[:top_k]]

    logger.info(f"Retrieved {len(top_chunk_texts)} chunks for user {user_id} via Hybrid Search")
    return top_chunk_texts