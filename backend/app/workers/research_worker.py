"""
Celery worker entrypoint.

Run with:
    celery -A app.workers.research_worker worker --loglevel=info

This is what makes POST /research return instantly with a session_id
while the actual multi-minute pipeline (planning -> search -> evidence
-> synthesis) runs in the background, per the async-processing
requirement in the architecture doc.
"""
import asyncio
import uuid

from celery import Celery

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.database import SessionLocal
from app.services.research_service import run_research_pipeline

settings = get_settings()
configure_logging()
logger = get_logger(__name__)

celery_app = Celery(
    "research_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]


@celery_app.task(name="run_research_pipeline_task", bind=True, max_retries=1)
def run_research_pipeline_task(self, session_id_str: str) -> None:
    """Celery entrypoint: bridges sync Celery task -> async pipeline function."""
    session_id = uuid.UUID(session_id_str)
    db = SessionLocal()
    try:
        logger.info("Starting research pipeline for session %s", session_id)
        asyncio.run(run_research_pipeline(db, session_id))
        logger.info("Finished research pipeline for session %s", session_id)
    finally:
        db.close()
