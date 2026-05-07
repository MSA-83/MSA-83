"""Export router for downloading data in various formats."""

import json

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from backend.services.auth.auth_service import get_current_user
from backend.services.conversation_service import conversation_service
from backend.services.export import CSVExporter, JSONExporter, MarkdownExporter, PDFExporter
from backend.services.usage_tracker import usage_tracker

router = APIRouter()


class ExportRequest(BaseModel):
    conversation_id: str
    format: str = "md"
    include_metadata: bool = False


@router.post("/conversation")
async def export_conversation(request: ExportRequest):
    """Export a conversation in the specified format (md, json, csv, pdf)."""
    if request.format not in ("md", "json", "csv", "pdf"):
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
    elif request.format == "pdf":
        content = PDFExporter.export_conversation(
            conversation["title"],
            messages,
            request.include_metadata,
        )
        media_type = "application/pdf"
        ext = "pdf"
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


@router.get("/gdpr/me")
async def export_my_data(current_user: dict = Depends(get_current_user)):
    """Export all personal data for the authenticated user (GDPR compliance)."""
    user_id = current_user["user_id"]
    email = current_user["email"]

    conversations = conversation_service.get_user_conversations(user_id)
    usage = usage_tracker.get_user_usage(user_id, days=365)

    export_data = {
        "export_type": "gdpr_personal_data",
        "user": {
            "id": user_id,
            "email": email,
            "tier": current_user.get("tier", "free"),
        },
        "conversations": [
            {
                "id": c["id"],
                "title": c["title"],
                "created_at": c.get("created_at"),
                "message_count": len(conversation_service.get_messages(c["id"], limit=10000)),
                "messages": conversation_service.get_messages(c["id"], limit=10000),
            }
            for c in conversations
        ],
        "usage": usage,
        "exported_at": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
    }

    content = json.dumps(export_data, indent=2, default=str)

    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="gdpr_export_{user_id}.json"',
        },
    )
