from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database.db import init_db
from app.routes import analytics, upload, violations

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix=settings.api_prefix, tags=["upload"])
app.include_router(violations.router, prefix=settings.api_prefix, tags=["violations"])
app.include_router(analytics.router, prefix=settings.api_prefix, tags=["analytics"])

# Serve generated evidence images
app.mount("/evidence", StaticFiles(directory=settings.evidence_dir), name="evidence")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}
