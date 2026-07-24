from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class DocumentAnalysisResponse(BaseModel):
    category: str
    confidence_score: float
    analysis_reason: str
    summary: str
    suggested_filename: str
    file_hash: str
    document_date: Optional[str] = None
    source: Optional[str] = None

class DocumentFinalizeRequest(BaseModel):
    category: str
    final_filename: str
    original_filename: str
    file_path: str
    file_hash: str
    confidence_score: Optional[float] = 1.0
    analysis_reason: Optional[str] = ""
    summary: Optional[str] = ""
    document_date: Optional[str] = None

class DocumentResponse(BaseModel):
    id: int
    doc_id: UUID
    user_id: Optional[int]
    original_filename: str
    category: str
    confidence_score: float
    analysis_reason: str
    summary: str
    suggested_filename: str
    document_date: Optional[str] = None
    file_hash: str
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentAnalysisResult(BaseModel):
    status: str
    message: Optional[str] = None
    data: Optional[DocumentResponse] = None
    analysis: Optional[DocumentAnalysisResponse] = None

from typing import List

class BatchDocumentAnalysisResult(BaseModel):
    status: str
    total_files: int
    results: List[DocumentAnalysisResult]

class UserResponse(BaseModel):
    username: str
    full_name: str
    role: str

    class Config:
        from_attributes = True
