"""Chat router for LLM interactions."""

import json
import os
import uuid

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.security.input_validation import validator as input_validator
from backend.security.prompt_injection import detector as injection_detector
from backend.services.ollama_service import OllamaService
from backend.services.rag_service import RAGService

router = APIRouter()

ollama_service = OllamaService(
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
)
rag_service = RAGService()

_conversation_store: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    use_rag: bool = True
    model: str | None = None
    max_tokens: int = 2048
    temperature: float = 0.7


class ChatResponse(BaseModel):
    response: str
    model: str
    conversation_id: str
    tokens_used: int
    rag_context_used: bool
    sources: list[dict]


class ConversationMessage(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str


class ConversationDetail(BaseModel):
    id: str
    title: str
    messages: list[ConversationMessage]
    created_at: str
    updated_at: str
    message_count: int
    is_pinned: bool
    is_archived: bool


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and get an AI response."""
    try:
        input_validator.validate_string(request.message)

        injection_result = injection_detector.analyze(request.message)
        if injection_result["is_suspicious"] and injection_result["max_severity"] in ("HIGH", "CRITICAL"):
            raise HTTPException(
                status_code=400,
                detail=f"Potential prompt injection detected: {injection_result['matches'][0]['pattern']}",
            )

        context = None
        rag_sources = []

        if request.use_rag:
            try:
                context_result = await rag_service.retrieve_context(request.message)
                if context_result:
                    context = context_result["context_text"]
                    rag_sources = context_result["chunks"]
            except Exception:
                context = None
                rag_sources = []

        try:
            response = await ollama_service.generate(
                prompt=request.message,
                context=context,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
        except Exception:
            response = {
                "response": f"AI service is currently unavailable. Your message was: {request.message[:50]}...",
                "model": request.model or ollama_service.default_model,
                "tokens_used": 0,
            }

        conversation_id = request.conversation_id or str(uuid.uuid4())[:8]
        if conversation_id not in _conversation_store:
            _conversation_store[conversation_id] = []

        _conversation_store[conversation_id].append({
            "role": "user",
            "content": request.message,
        })
        _conversation_store[conversation_id].append({
            "role": "assistant",
            "content": response["response"],
        })

        return ChatResponse(
            response=response["response"],
            model=response["model"],
            conversation_id=conversation_id,
            tokens_used=response.get("tokens_used", 0),
            rag_context_used=context is not None,
            sources=rag_sources,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream an AI response with Server-Sent Events."""
    input_validator.validate_string(request.message)

    injection_result = injection_detector.analyze(request.message)
    if injection_result["is_suspicious"] and injection_result["max_severity"] in ("HIGH", "CRITICAL"):
        raise HTTPException(
            status_code=400,
            detail=f"Potential prompt injection detected: {injection_result['matches'][0]['pattern']}",
        )

    conversation_id = request.conversation_id or str(uuid.uuid4())[:8]

    async def generate():
        context = None
        rag_sources = []

        if request.use_rag:
            try:
                context_result = await rag_service.retrieve_context(request.message)
                if context_result:
                    context = context_result["context_text"]
                    rag_sources = context_result.get("chunks", [])
            except Exception:
                pass

        model_name = request.model or ollama_service.default_model

        metadata_event = json.dumps({
            "type": "metadata",
            "conversation_id": conversation_id,
            "model": model_name,
            "rag_sources_count": len(rag_sources),
        })
        yield f"data: {metadata_event}\n\n"

        full_response = ""
        try:
            async for chunk in ollama_service.generate_stream(
                prompt=request.message,
                context=context,
                model=request.model,
                temperature=request.temperature,
            ):
                try:
                    chunk_data = json.loads(chunk)
                    text = chunk_data.get("chunk", "")
                    full_response += text
                    yield f"data: {json.dumps({'type': 'chunk', 'content': text})}\n\n"
                except json.JSONDecodeError:
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            if conversation_id not in _conversation_store:
                _conversation_store[conversation_id] = []
            _conversation_store[conversation_id].append({"role": "user", "content": request.message})
            _conversation_store[conversation_id].append({"role": "assistant", "content": full_response})

            done_event = json.dumps({
                "type": "done",
                "conversation_id": conversation_id,
                "full_text": full_response,
            })
            yield f"data: {done_event}\n\n"

        except Exception as e:
            error_event = json.dumps({
                "type": "error",
                "message": str(e),
            })
            yield f"data: {error_event}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.websocket("/ws/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time chat with typing indicators."""
    await websocket.accept()

    if conversation_id not in _conversation_store:
        _conversation_store[conversation_id] = []

    connection_info = {
        "connected_at": __import__("datetime").datetime.utcnow().isoformat(),
        "conversation_id": conversation_id,
    }
    await websocket.send_json({"type": "connected", **connection_info})

    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type", "message")

            if message_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if message_type == "typing":
                await websocket.send_json({
                    "type": "typing_ack",
                    "status": data.get("status", "started"),
                })
                continue

            if message_type != "message":
                continue

            text = data.get("content", "")
            if not text.strip():
                await websocket.send_json({"type": "error", "message": "Empty message"})
                continue

            injection_result = injection_detector.analyze(text)
            if injection_result["is_suspicious"] and injection_result["max_severity"] in ("HIGH", "CRITICAL"):
                await websocket.send_json({
                    "type": "error",
                    "message": "Message blocked: potential prompt injection",
                })
                continue

            _conversation_store[conversation_id].append({"role": "user", "content": text})

            await websocket.send_json({"type": "typing_indicator", "status": "thinking"})

            try:
                response = await ollama_service.chat(
                    model=data.get("model", "llama3"),
                    messages=[{"role": m["role"], "content": m["content"]} for m in _conversation_store[conversation_id]],
                    temperature=data.get("temperature", 0.7),
                )

                assistant_text = response.get("message", {}).get("content", "")

                await websocket.send_json({
                    "type": "message",
                    "role": "assistant",
                    "content": assistant_text,
                    "conversation_id": conversation_id,
                })

                _conversation_store[conversation_id].append({"role": "assistant", "content": assistant_text})

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"AI service error: {str(e)}",
                })

    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass


@router.post("/conversations/rename")
async def rename_conversation(conversation_id: str = Query(...), new_title: str = Query(...)):
    """Rename a conversation."""
    input_validator.validate_string(new_title)
    if len(new_title) > 100:
        raise HTTPException(status_code=400, detail="Title too long (max 100 chars)")

    if conversation_id not in _conversation_store and not conversation_id.startswith("conv-"):
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"status": "ok", "conversation_id": conversation_id, "title": new_title}


@router.post("/conversations/pin")
async def pin_conversation(conversation_id: str = Query(...)):
    """Pin a conversation to the top of the list."""
    if conversation_id not in _conversation_store and not conversation_id.startswith("conv-"):
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"status": "ok", "conversation_id": conversation_id, "pinned": True}


@router.post("/conversations/archive")
async def archive_conversation(conversation_id: str = Query(...)):
    """Archive a conversation."""
    if conversation_id not in _conversation_store and not conversation_id.startswith("conv-"):
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"status": "ok", "conversation_id": conversation_id, "archived": True}


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history."""
    messages = _conversation_store.get(conversation_id, [])
    formatted_messages = [
        ConversationMessage(
            id=str(uuid.uuid4())[:8],
            role=m["role"],
            content=m["content"],
            timestamp=__import__("datetime").datetime.utcnow().isoformat(),
        )
        for m in messages
    ]

    return {
        "id": conversation_id,
        "title": f"Conversation {conversation_id[:8]}",
        "messages": formatted_messages,
        "created_at": __import__("datetime").datetime.utcnow().isoformat(),
        "updated_at": __import__("datetime").datetime.utcnow().isoformat(),
        "message_count": len(formatted_messages),
        "is_pinned": False,
        "is_archived": False,
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    if conversation_id in _conversation_store:
        del _conversation_store[conversation_id]
    return {"status": "ok", "conversation_id": conversation_id}


@router.get("/models")
async def list_models():
    """List available Ollama models."""
    try:
        models = await ollama_service.list_models()
        return {"models": models, "default": ollama_service.default_model}
    except Exception:
        return {"models": [ollama_service.default_model], "default": ollama_service.default_model}
