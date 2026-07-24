import os
import logging
import hashlib
from sqlalchemy.orm import Session
from app.domain.entities import DocumentHistory, User
from app.domain.schemas import DocumentFinalizeRequest, DocumentResponse

logger = logging.getLogger(__name__)

def finalize_document(db: Session, request: DocumentFinalizeRequest, current_user: User) -> DocumentResponse:
    """
    Menyimpan metadata dokumen ke database berdasarkan path yang diberikan oleh Flutter.
    """
    try:
        new_doc = DocumentHistory(
            user_id=current_user.id,
            original_filename=request.original_filename,
            category=request.category,
            confidence_score=request.confidence_score,
            analysis_reason=request.analysis_reason,
            summary=request.summary,
            suggested_filename=request.final_filename,
            document_date=request.document_date,
            file_hash=request.file_hash,
            file_path=request.file_path
        )
        
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        
        return DocumentResponse.model_validate(new_doc)

    except Exception as e:
        logger.error(f"[finalize_document] Database error: {e}")
        db.rollback()
        raise e