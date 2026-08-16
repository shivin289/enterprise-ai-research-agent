"""
Internal document upload + indexing. This is what lets the demo show:
"upload company_ai_strategy.pdf, re-run research, watch it incorporate
the new business context without touching source code."
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentOut, DocumentUploadResponse
from app.retrieval.vector_store import index_document

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    raw_bytes = await file.read()
    if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 10MB limit")

    text_content = _extract_text(raw_bytes, ext)

    document = Document(
        tenant_id=current_user.tenant_id,
        filename=file.filename,
        source="upload",
        content=text_content,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    chunks_created = await index_document(db, document)

    return DocumentUploadResponse(document_id=document.id, filename=document.filename, chunks_created=chunks_created)


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    docs = db.query(Document).filter(Document.tenant_id == current_user.tenant_id).all()
    return [DocumentOut.model_validate(d) for d in docs]


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.get(Document, document_id)
    if doc is None or doc.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()


def _extract_text(raw_bytes: bytes, ext: str) -> str:
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            import io

            reader = PdfReader(io.BytesIO(raw_bytes))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="PDF support requires the 'pypdf' package. Add it to requirements.txt.",
            )
    return raw_bytes.decode("utf-8", errors="ignore")
