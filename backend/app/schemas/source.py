import uuid
from datetime import datetime

from pydantic import BaseModel


class SourceOut(BaseModel):
    id: uuid.UUID
    title: str
    url: str | None
    publisher: str | None
    published_at: datetime | None
    source_type: str
    reliability_score: float

    class Config:
        from_attributes = True
