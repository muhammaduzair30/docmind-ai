from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    upload_time = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="documents")