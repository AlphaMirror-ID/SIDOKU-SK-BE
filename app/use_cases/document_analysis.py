import os
import datetime
import re
import time
import logging
from typing import Optional
from app.infrastructure.text_extractors import extract_text
from app.infrastructure.gemini_client import classify_document
from app.infrastructure.file_storage import delete_temp_file

logger = logging.getLogger(__name__)

def analyze_document(temp_path: str, original_filename: str, created_date: Optional[str] = None) -> dict:
    start_extraction = time.perf_counter()
    text_content = extract_text(temp_path)
    extraction_duration = time.perf_counter() - start_extraction
    logger.info(f"[LOG] 2. Ekstraksi Teks Selesai: {extraction_duration:.4f} detik")
    
    if not text_content or not text_content.strip():
        delete_temp_file(temp_path)
        return {"error": "Gagal membaca dokumen: Tidak ada teks yang terdeteksi."}
        
    letters_only = re.sub(r'[^a-zA-Z]', '', text_content)
    if len(letters_only) < 10:
        delete_temp_file(temp_path)
        return {"error": "Dokumen ditolak: Teks yang terdeteksi terlalu sedikit atau tidak bermakna (kemungkinan besar bukan dokumen teks/surat resmi)."}
    
    start_classification = time.perf_counter()
    gemini_result = classify_document(text_content)
    classification_duration = time.perf_counter() - start_classification
    logger.info(f"[LOG] 3. Klasifikasi AI (Gemini) Selesai: {classification_duration:.4f} detik")
    
    if "error" in gemini_result:
        delete_temp_file(temp_path)
        return gemini_result
        
    ext = os.path.splitext(original_filename)[1].lower()
    
    if not gemini_result.get('document_date'):
        fallback_date = None
        if created_date:
            fallback_date = created_date
        else:
            try:
                file_stat = os.stat(temp_path)
                timestamp = file_stat.st_mtime 
                fallback_date = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            except Exception as e:
                logger.warning(f"Gagal mengambil metadata file: {e}")
        
        gemini_result['document_date'] = fallback_date
        
        if fallback_date:
            suggested = gemini_result.get('suggested_filename', 'Untitled')
            if fallback_date not in suggested:
                gemini_result['suggested_filename'] = f"{suggested}_{fallback_date}"

    suggested_name = f"{gemini_result.get('suggested_filename', 'Untitled')}{ext}"
    gemini_result['suggested_filename'] = suggested_name
    gemini_result['source'] = 'ai'
    gemini_result['temp_path'] = temp_path
    
    return gemini_result