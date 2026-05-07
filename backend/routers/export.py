"""Export router for downloading data in various formats."""

import json

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from backend.services.conversation_service import conversation_service
from backend.services.export import CSVExporter, JSONExporter, MarkdownExporter
from backend.services.usage_tracker import usage_tracker

router = APIRouter()


class ExportRequest(BaseModel):
    conversation_id: str
    format: str = "md"
    include_metadata: bool = False


@router.post("/conversation")
async def export_conversation(request: ExportRequest):
    """Export a conversation in the specified format."""
    if request.format not in ("md", "json", "csv"):
        raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")

    conversation = conversation_service.get_conversation(request.conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = conversation_service.get_messages(request.conversation_id, limit=1000)

    if request.format == "md":
        content = MarkdownExporter.export_conversation(
            conversation["title"],
            messages,
            request.include_metadata,
        )
        media_type = "text/markdown"
        ext = "md"
    elif request.format == "json":
        content = JSONExporter.export_conversation(
            request.conversation_id,
            conversation["title"],
            messages,
        )
        media_type = "application/json"
        ext = "json"
    else:
        content = CSVExporter.export_conversation(messages)
        media_type = "text/csv"
        ext = "csv"

    filename = f"{conversation['title'][:30].replace(' ', '_')}.{ext}"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/usage/{user_id}")
async def export_usage(user_id: str, format: str = "json", days: int = 30):
    """Export usage data."""
    usage = usage_tracker.get_user_usage(user_id, days)

    if format == "json":
        content = JSONExporter.export_usage_report(user_id, usage)
        media_type = "application/json"
        ext = "json"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="usage_{user_id}.{ext}"',
        },
    )


@router.get("/memory")
async def export_memory(
    query: str | None = None,
    format: str = "md",
):
    """Export memory data."""
    from backend.services.rag_service import RAGService

    rag_service = RAGService()

    if query:
        result = await rag_service.retrieve_context(query, top_k=100)
        chunks = result.get("chunks", []) if result else []
    else:
        chunks = []

    if format == "md":
        content = MarkdownExporter.export_memory_chunks(chunks)
        media_type = "text/markdown"
        ext = "md"
    elif format == "json":
        content = json.dumps({"chunks": chunks}, indent=2)
        media_type = "application/json"
        ext = "json"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="memory_export.{ext}"',
        },
    )
