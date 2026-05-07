"""Conversations router for chat history management."""


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.conversation_service import conversation_service

router = APIRouter()


class CreateConversationRequest(BaseModel):
    title: str | None = None


class AddMessageRequest(BaseModel):
    role: str
    content: str
    metadata: dict | None = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


@router.post("/", response_model=ConversationResponse)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    conversation = conversation_service.create_conversation(
        user_id="anonymous",
        title=request.title,
    )
    return conversation


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total: int


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(limit: int = 20, offset: int = 0):
    """List all conversations."""
    conversations = conversation_service.get_conversations(
        user_id="anonymous",
        limit=limit,
        offset=offset,
    )
    return ConversationListResponse(
        conversations=conversations,
        total=len(conversations),
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """Get a conversation by ID."""
    conversation = conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
):
    """Get messages for a conversation."""
    if not conversation_service.get_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = conversation_service.get_messages(
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
    )
    return messages


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: str,
    request: AddMessageRequest,
):
    """Add a message to a conversation."""
    try:
        message = conversation_service.add_message(
            conversation_id=conversation_id,
            role=request.role,
            content=request.content,
            metadata=request.metadata,
        )
        return message
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{conversation_id}/title", response_model=ConversationResponse)
async def update_title(conversation_id: str, title: str):
    """Update conversation title."""
    conversation = conversation_service.update_title(conversation_id, title)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    deleted = conversation_service.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"deleted": True}


@router.get("/search")
async def search_conversations(query: str):
    """Search conversations."""
    results = conversation_service.search_conversations(
        user_id="anonymous",
        query=query,
    )
    return results


@router.get("/stats")
async def get_stats():
    """Get conversation statistics."""
    return conversation_service.get_stats(user_id="anonymous")
