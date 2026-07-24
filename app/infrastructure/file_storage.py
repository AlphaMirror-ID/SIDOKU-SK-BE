import os
import shutil
import uuid
import logging

logger = logging.getLogger(__name__)

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

def save_temp_file(file_bytes: bytes, original_filename: str) -> str:
    """Menyimpan file sementara ke folder temp sebelum diproses oleh AI."""
    temp_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_{original_filename}")
    with open(temp_path, "wb") as buffer:
        buffer.write(file_bytes)
    return temp_path

def delete_temp_file(temp_path: str):
    """Menghapus file temp setelah selesai diproses AI."""
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception as e:
            logger.warning(f"Gagal menghapus file temp '{temp_path}': {e}")