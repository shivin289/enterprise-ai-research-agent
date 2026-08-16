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
    # No Alembic migrations wired up yet, so we create tables on every
    # startup regardless of environment. Safe to run repeatedly --
    # create_all() only creates tables that don't already exist.
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
    allow_origins=[
        "http://localhost:5173",
        "https://enterprise-ai-research-agent-1b78.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(research.router)
app.include_router(sources.router)
app.include_router(documents.router)
