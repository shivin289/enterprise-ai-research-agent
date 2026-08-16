"""
pgvector-backed similarity search over internal document chunks.
Kept separate from the external web search_provider so the research
engine can blend "what the internet says" with "what our own uploaded
documents say" without either side knowing about the other's storage.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.embeddings import embed_texts
from app.models.document import Document, DocumentChunk


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Simple sliding-window chunker. Good enough for MVP; swap for a
    semantic/structure-aware chunker (e.g. by heading) for production docs."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
        if start < 0 or end >= len(text):
            break
    return [c for c in chunks if c.strip()]


async def index_document(db: Session, document: Document) -> int:
    """Chunk + embed a document's content and persist chunks with vectors."""
    chunks = chunk_text(document.content)
    if not chunks:
        return 0

    vectors = await embed_texts(chunks)

    for text, vector in zip(chunks, vectors):
        db.add(DocumentChunk(document_id=document.id, content=text, embedding=vector))

    db.commit()
    return len(chunks)


async def similarity_search(db: Session, query: str, tenant_id, top_k: int = 5) -> list[DocumentChunk]:
    """Return the top_k most similar document chunks to `query` for this tenant."""
    [query_vector] = await embed_texts([query])

    stmt = (
        select(DocumentChunk)
        .join(Document)
        .where(Document.tenant_id == tenant_id)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
        .limit(top_k)
    )
    return list(db.execute(stmt).scalars().all())
