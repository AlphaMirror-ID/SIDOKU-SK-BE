from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(60), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(String(50), default="staff")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DocumentHistory(Base):
    __tablename__ = "document_histories"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) 
    original_filename = Column(String(255), nullable=False)
    category = Column(String(100))
    confidence_score = Column(Float)
    analysis_reason = Column(Text)
    summary = Column(Text)
    suggested_filename = Column(String(255))
    document_date = Column(String(10))
    file_hash = Column(String(64), index=True)
    file_path = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())