"""
FastAPI application entrypoint.
    uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, auth, research, sources, documents
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.database import Base, engine

settings = get_settings()
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # For local dev/demo, auto-create tables. In production, use Alembic
    # migrations (see app/db/migrations/) instead of create_all.
    if settings.app_env == "development":
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Enterprise AI Research Agent",
    description="A modular RAG research system with source citations, "
                 "evidence validation, conflict detection, and explainable reports.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(research.router)
app.include_router(sources.router)
app.include_router(documents.router)
