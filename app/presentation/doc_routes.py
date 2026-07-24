from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
import time
import logging
import json
from typing import List, Optional
from app.domain.schemas import DocumentFinalizeRequest, DocumentResponse, DocumentAnalysisResult, DocumentAnalysisResponse
from app.domain.entities import User, DocumentHistory
from app.presentation.dependencies import get_db, get_current_user
from app.use_cases.document_upload import calculate_hash, check_duplicate_or_clone
from app.use_cases.document_analysis import analyze_document
from app.use_cases.document_finalize import finalize_document
from app.infrastructure.file_storage import save_temp_file, delete_temp_file
from fastapi.responses import FileResponse

import os
import shutil

logger = logging.getLogger(__name__)
BACKUP_DIR = os.path.join("storage", "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

router = APIRouter(tags=["Documents"])

@router.post("/analyze", response_model=DocumentAnalysisResult)
async def analyze(
    file: UploadFile = File(...),
    x_file_created_dates: Optional[str] = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_total = time.perf_counter()
    logger.info(f"=== [START] Proses Analisis Berkas: {file.filename} ===")
    
    start_upload = time.perf_counter()
    file_bytes = await file.read()
    file_hash = calculate_hash(file_bytes)
    upload_duration = time.perf_counter() - start_upload
    logger.info(f"[LOG] 1. Pembacaan & Upload Berkas Selesai: {upload_duration:.4f} detik (Hash: {file_hash})")
    
    check_result = check_duplicate_or_clone(db, file_hash, current_user)
    
    if check_result:
      if check_result.status == "skipped":
            logger.info(f"[LOG] Proses dihentikan: Dokumen sudah pernah diupload.")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dokumen sudah pernah diupload.")
      elif check_result.status == "clone":
            total_duration = time.perf_counter() - start_total
            logger.info(f"[LOG] Proses selesai (CLONE): {total_duration:.4f} detik")
            logger.info(f"=== [END] Proses Analisis Berkas Selesai ===")
            return check_result
 
    temp_path = save_temp_file(file_bytes, file.filename)
    
    created_date = None
    if x_file_created_dates:
        try:
            dates_map = json.loads(x_file_created_dates)
            created_date = dates_map.get(file.filename)
        except Exception as e:
            logger.warning(f"Gagal memparse header X-File-Created-Dates: {e}")

    try:
        analysis_dict = analyze_document(temp_path, file.filename, created_date)
        
        if "error" in analysis_dict:
            logger.error(f"[LOG] Error analisis dokumen {file.filename}: {analysis_dict['error']}")
            raise HTTPException(status_code=500, detail=analysis_dict["error"])
            
        analysis_dict["file_hash"] = file_hash
        analysis_response = DocumentAnalysisResponse(**analysis_dict)
        
        backup_path = os.path.join(BACKUP_DIR, file_hash)
        if not os.path.exists(backup_path):
            shutil.copy2(temp_path, backup_path)
            logger.info(f"[LOG] File berhasil di-backup ke server: {backup_path}")

        total_duration = time.perf_counter() - start_total
        logger.info(f"[LOG] 4. Total Waktu Proses (Upload->Ekstraksi->Klasifikasi): {total_duration:.4f} detik")
        logger.info(f"=== [END] Proses Analisis Berkas Selesai ===")
        
        return DocumentAnalysisResult(
            status="success",
            message="Dokumen berhasil dianalisis",
            analysis=analysis_response
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[LOG] Gagal menganalisis dokumen {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gagal memproses dokumen: {str(e)}")
    finally:
        delete_temp_file(temp_path)

@router.post("/finalize-and-save", response_model=DocumentResponse)
def finalize_and_save(
    request: DocumentFinalizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return finalize_document(db, request, current_user)
    except Exception as e:
        err_msg = str(e)
        if isinstance(e, PermissionError) or "Akses ditolak" in err_msg:
            raise HTTPException(status_code=403, detail=err_msg)
        if isinstance(e, OSError) and ("Kapasitas" in err_msg or "penyimpanan" in err_msg.lower()):
            raise HTTPException(status_code=507, detail=err_msg)
        if isinstance(e, FileNotFoundError):
            raise HTTPException(status_code=404, detail=err_msg)
        if "unique" in err_msg.lower() or "duplicate" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dokumen sudah ditambahkan oleh pengguna lain.")
        raise HTTPException(status_code=500, detail=err_msg)

from typing import List, Optional
from app.domain.schemas import BatchDocumentAnalysisResult

@router.get("/documents", response_model=List[DocumentResponse])
def get_documents(
    search: Optional[str] = None,
    category: Optional[str] = None,
    year: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(DocumentHistory).filter(DocumentHistory.user_id == current_user.id)
    
    if category and category.lower() != "semua":
        category_map = {
            "kependudukan": "Layanan Kependudukan",
            "layanan kependudukan": "Layanan Kependudukan",
            "administrasi umum": "Administrasi Umum",
            "keuangan": "Keuangan & Anggaran",
            "keuangan & anggaran": "Keuangan & Anggaran",
            "pembangunan": "Pembangunan & Proyek",
            "pembangunan & proyek": "Pembangunan & Proyek",
            "kesra": "Kesejahteraan Sosial",
            "kesejahteraan sosial": "Kesejahteraan Sosial",
            "pertanahan": "Pertanahan & Perkebunan",
            "pertanahan & perkebunan": "Pertanahan & Perkebunan",
            "pemberdayaan": "Pemberdayaan Masyarakat",
            "pemberdayaan masyarakat": "Pemberdayaan Masyarakat",
            "keamanan": "Keamanan & Ketertiban",
            "keamanan & ketertiban": "Keamanan & Ketertiban",
            "pendidikan": "Pendidikan",
            "lainnya": "Lainnya"
        }
        mapped_category = category_map.get(category.lower())
        if mapped_category:
            query = query.filter(DocumentHistory.category == mapped_category)
        else:
            query = query.filter(DocumentHistory.category.ilike(f"%{category}%"))
            
    if year:
        query = query.filter(DocumentHistory.document_date.like(f"{year}%"))
        
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (DocumentHistory.suggested_filename.ilike(search_filter)) |
            (DocumentHistory.original_filename.ilike(search_filter)) |
            (DocumentHistory.summary.ilike(search_filter)) |
            (DocumentHistory.category.ilike(search_filter))
        )
        
    return query.order_by(DocumentHistory.created_at.desc()).all()

@router.get("/documents/{doc_id}/download")
def download_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(DocumentHistory).filter(
        DocumentHistory.doc_id == doc_id,
        DocumentHistory.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
        
    backup_path = os.path.join(BACKUP_DIR, doc.file_hash)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="File backup tidak ditemukan di server")
        
    return FileResponse(
        path=backup_path,
        media_type="application/octet-stream",
        filename=doc.suggested_filename
    )

@router.post("/analyze-batch", response_model=BatchDocumentAnalysisResult)
async def analyze_batch(
    files: List[UploadFile] = File(...),
    x_file_created_dates: Optional[str] = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_batch = time.perf_counter()
    logger.info(f"=== [START BATCH] Memproses {len(files)} berkas ===")
    
    results = []
    
    for idx, file in enumerate(files, 1):
        try:
            start_total = time.perf_counter()
            logger.info(f"--- [BATCH FILE {idx}/{len(files)}] Memulai Analisis Berkas: {file.filename} ---")
            
            start_upload = time.perf_counter()
            file_bytes = await file.read()
            file_hash = calculate_hash(file_bytes)
            upload_duration = time.perf_counter() - start_upload
            logger.info(f"[LOG] 1. Pembacaan & Upload Berkas Selesai: {upload_duration:.4f} detik (Hash: {file_hash})")
            
            check_result = check_duplicate_or_clone(db, file_hash, current_user)
            
            if check_result:
                if check_result.status == "clone":
                    results.append(check_result)
                    total_duration = time.perf_counter() - start_total
                    logger.info(f"[LOG] Berkas ini dilewati (CLONE) dalam {total_duration:.4f} detik")
                else:
                    logger.info(f"[LOG] Berkas ini dilewati (SKIPPED/DUPLICATE)")
                continue
                
            temp_path = save_temp_file(file_bytes, file.filename)
            
            created_date = None
            if x_file_created_dates:
                try:
                    dates_map = json.loads(x_file_created_dates)
                    created_date = dates_map.get(file.filename)
                except Exception as e:
                    pass

            try:
                analysis_dict = analyze_document(temp_path, file.filename, created_date)
                
                if "error" in analysis_dict:
                    results.append(DocumentAnalysisResult(status="error", message=analysis_dict["error"]))
                    logger.error(f"[LOG] Error saat menganalisis berkas {file.filename}: {analysis_dict['error']}")
                    continue
                    
                analysis_dict["file_hash"] = file_hash
                analysis_response = DocumentAnalysisResponse(**analysis_dict)
                
                # Backup file to server with de-duplication based on hash
                backup_path = os.path.join(BACKUP_DIR, file_hash)
                if not os.path.exists(backup_path):
                    shutil.copy2(temp_path, backup_path)
                    logger.info(f"[LOG] File berhasil di-backup ke server (Batch): {backup_path}")

                results.append(DocumentAnalysisResult(status="success", message="Dokumen berhasil dianalisis", analysis=analysis_response))
                
                total_duration = time.perf_counter() - start_total
                logger.info(f"[LOG] 4. Berkas berhasil dianalisis dalam {total_duration:.4f} detik")
            finally:
                delete_temp_file(temp_path)
            
        except Exception as e:
            results.append(DocumentAnalysisResult(status="error", message=str(e)))
            logger.error(f"[LOG] Gagal memproses berkas {file.filename}: {e}", exc_info=True)
            
    batch_duration = time.perf_counter() - start_batch
    logger.info(f"=== [END BATCH] Memproses {len(files)} berkas selesai dalam {batch_duration:.4f} detik ===")
    return BatchDocumentAnalysisResult(status="batch_completed", total_files=len(files), results=results)

@router.post("/finalize-and-save-batch", response_model=List[DocumentResponse])
def finalize_and_save_batch(
    requests_list: List[DocumentFinalizeRequest],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = []
    for req in requests_list:
        try:
            doc = finalize_document(db, req, current_user)
            results.append(doc)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal memproses {req.final_filename}: {str(e)}")
            
    return results