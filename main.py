import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(message)s",
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