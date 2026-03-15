from sqlalchemy.orm import Session
from app.services.retrieval_service import retrieve_chunks
from app.services.llm_service import generate_answer
from app.core.logging import logger

def ask_question(db: Session, question: str, user_id: int, top_k: int = 5) -> str:
    """
    Full RAG pipeline orchestration:
    1. Retrieve relevant document chunks via pgvector similarity search
    2. Check if chunks were retrieved; if not, return default empty message
    3. Generate an answer using the Gemini LLM with retrieved context
    4. Return the answer string
    """

    # Step 1: Retrieve relevant chunks
    chunks = retrieve_chunks(db=db, question=question, user_id=user_id, top_k=top_k)

    # Step 2: Handle empty context immediately
    if not chunks:
        logger.info(f"No relevant chunks found for user {user_id} query: {question}")
        return "The document does not contain this information."

    # Step 3: Generate answer using LLM
    try:
        answer = generate_answer(question=question, chunks=chunks)
        return answer
    except Exception as e:
        logger.error(f"LLM generation failed: {str(e)}")
        raise Exception("Failed to generate answer from the AI model.")
