from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import TSVECTOR
from pgvector.sqlalchemy import Vector
from app.db.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_text = Column(Text)
    embedding = Column(Vector(384))
    fts_tokens = Column(TSVECTOR)
