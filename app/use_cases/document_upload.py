import hashlib
from sqlalchemy.orm import Session
from app.domain.entities import DocumentHistory, User
from app.domain.schemas import DocumentAnalysisResult, DocumentResponse

def calculate_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

def check_duplicate_or_clone(db: Session, file_hash: str, current_user: User) -> DocumentAnalysisResult:
    my_existing_doc = db.query(DocumentHistory).filter(
        DocumentHistory.file_hash == file_hash, 
        DocumentHistory.user_id == current_user.id
    ).first()
    
    if my_existing_doc:
        return DocumentAnalysisResult(
            status="skipped",
            message="Dokumen ini sudah ada di arsip Anda",
            data=DocumentResponse.model_validate(my_existing_doc)
        )
    
    any_existing_doc = db.query(DocumentHistory).filter(DocumentHistory.file_hash == file_hash).first()
    
    if any_existing_doc:
        return DocumentAnalysisResult(
            status="clone",
            message="Dokumen identik ditemukan di sistem.",
            analysis={
                "category": any_existing_doc.category,
                "confidence_score": any_existing_doc.confidence_score,
                "analysis_reason": any_existing_doc.analysis_reason,
                "summary": any_existing_doc.summary,
                "suggested_filename": any_existing_doc.suggested_filename,
                "document_date": any_existing_doc.document_date,
                "file_hash": file_hash,
                "source": "clone"
            }
        )
        
    return None