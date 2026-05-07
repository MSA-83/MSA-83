"""Memory router for RAG document management."""


from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.security.input_validation import validator as input_validator
from backend.services.processing.file_processor import FileUploadHandler
from backend.services.rag_service import RAGService

router = APIRouter()
rag_service = RAGService()
file_handler = FileUploadHandler()


class IngestRequest(BaseModel):
    text: str
    source: str | None = None
    metadata: dict | None = None
    chunker_strategy: str = "fixed"


class IngestResponse(BaseModel):
    document_id: str
    chunks_processed: int
    chunks_stored: int
    errors: list[str]


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    min_score: float = 0.0
    filter_metadata: dict | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[dict]
    total_results: int


class FileUploadResponse(BaseModel):
    file_name: str
    document_id: str
    chunks_processed: int
    chunks_stored: int
    char_count: int
    word_count: int
    errors: list[str]


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest):
    """Ingest a text document into the memory system."""
    result = await rag_service.ingest(
        text=request.text,
        source=request.source,
        metadata=request.metadata,
        chunker_strategy=request.chunker_strategy,
    )

    return IngestResponse(**result)


@router.post("/ingest-file", response_model=FileUploadResponse)
async def ingest_file(
    file: UploadFile = File(...),
    source: str | None = None,
    chunker_strategy: str = "fixed",
):
    """Ingest an uploaded file (PDF, DOCX, TXT, MD, CSV, JSON) into the memory system."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    try:
        input_validator.validate_filename(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    content = await file.read()

    try:
        file_result = await file_handler.process_upload(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    chunker = "markdown" if file_result["extension"] == ".md" else chunker_strategy

    result = await rag_service.ingest(
        text=file_result["content"],
        source=source or file.filename,
        chunker_strategy=chunker,
    )

    return FileUploadResponse(
        file_name=file_result["file_name"],
        document_id=result["document_id"],
        chunks_processed=result["chunks_processed"],
        chunks_stored=result["chunks_stored"],
        char_count=file_result["char_count"],
        word_count=file_result["word_count"],
        errors=result["errors"],
    )


@router.post("/search", response_model=SearchResponse)
async def search_memory(request: SearchRequest):
    """Search the memory system for relevant context."""
    result = await rag_service.retrieve_context(
        query=request.query,
        top_k=request.top_k,
        min_score=request.min_score,
        filter_metadata=request.filter_metadata,
    )

    if not result:
        return SearchResponse(
            query=request.query,
            results=[],
            total_results=0,
        )

    return SearchResponse(
        query=request.query,
        results=result["chunks"],
        total_results=result["total_results"],
    )


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its chunks from memory."""
    deleted = await rag_service.delete_document(document_id)
    return {"deleted": deleted, "document_id": document_id}


@router.get("/stats")
async def get_memory_stats():
    """Get memory system statistics."""
    return await rag_service.get_stats()
