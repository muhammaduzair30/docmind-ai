from sqlalchemy.orm import Session
from typing import Dict

from app.services.retrieval_service import retrieve_chunks
from app.services.llm_service import generate_answer


def ask_question(db: Session, question: str, user_id: int) -> Dict:

    # Step 1: retrieve relevant chunks
    chunks = retrieve_chunks(db, question, user_id)

    # Step 2: generate answer
    answer = generate_answer(question, chunks)

    return {
        "question": question,
        "answer": answer,
        "sources": chunks
    }