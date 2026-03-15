import pytest
from unittest.mock import Mock, patch
from app.services.rag_service import ask_question

# Mock the database session
@pytest.fixture
def mock_db():
    return Mock()

def test_rag_service_empty_chunks(mock_db):
    """Test that rag_service returns a default response if no chunks are found without calling LLM."""
    
    with patch("app.services.rag_service.retrieve_chunks", return_value=[]) as mock_retrieve:
        with patch("app.services.rag_service.generate_answer") as mock_generate:
            
            answer = ask_question(mock_db, "What is the secret?", user_id=1)
            
            assert answer == "The document does not contain this information."
            mock_retrieve.assert_called_once_with(db=mock_db, question="What is the secret?", user_id=1, top_k=5)
            mock_generate.assert_not_called()

def test_rag_service_with_chunks(mock_db):
    """Test that rag_service calls LLM if chunks are found."""
    
    fake_chunks = ["chunk1", "chunk2"]
    fake_answer = "This is the generated answer."
    
    with patch("app.services.rag_service.retrieve_chunks", return_value=fake_chunks) as mock_retrieve:
        with patch("app.services.rag_service.generate_answer", return_value=fake_answer) as mock_generate:
            
            answer = ask_question(mock_db, "Tell me something", user_id=1)
            
            assert answer == fake_answer
            mock_retrieve.assert_called_once_with(db=mock_db, question="Tell me something", user_id=1, top_k=5)
            mock_generate.assert_called_once_with(question="Tell me something", chunks=fake_chunks)
