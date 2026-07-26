import os
from logging.handlers import TimedRotatingFileHandler

# Membuat folder logs jika belum ada
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Formatter log
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Handler untuk menampilkan log di terminal (Console)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Handler untuk menulis log ke file harian (Timed Rotating File)
file_handler = TimedRotatingFileHandler(
    os.path.join(log_dir, "app.log"),
    when="midnight",
    interval=1,
    backupCount=30,  # Menyimpan riwayat log selama 30 hari
    encoding="utf-8"
)
file_handler.setFormatter(log_formatter)

# Konfigurasi logging dasar
logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler, file_handler],
    force=True,
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.infrastructure.database import engine
from app.domain.entities import Base
from app.presentation.auth_routes import router as auth_router
from app.presentation.doc_routes import router as doc_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sukasari Kidul Document System (Clean Architecture)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(doc_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "API Klasifikasi Desa Sukasari Kidul Aktif (Clean Architecture)"}