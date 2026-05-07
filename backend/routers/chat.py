"""Chat router for LLM interactions."""

import os

from fastapi import APIRouter, HTTPException
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


class Conversation(BaseModel):
    id: str
    messages: list[dict]
    created_at: str


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

        return ChatResponse(
            response=response["response"],
            model=response["model"],
            conversation_id=request.conversation_id or "new",
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
    """Stream an AI response."""
    from fastapi.responses import StreamingResponse

    input_validator.validate_string(request.message)

    injection_result = injection_detector.analyze(request.message)
    if injection_result["is_suspicious"] and injection_result["max_severity"] in ("HIGH", "CRITICAL"):
        raise HTTPException(
            status_code=400,
            detail=f"Potential prompt injection detected: {injection_result['matches'][0]['pattern']}",
        )

    async def generate():
        context = None

        if request.use_rag:
            context_result = await rag_service.retrieve_context(request.message)
            if context_result:
                context = context_result["context_text"]

        async for chunk in ollama_service.generate_stream(
            prompt=request.message,
            context=context,
            model=request.model,
            temperature=request.temperature,
        ):
            yield f"data: {chunk}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get conversation history."""
    return Conversation(
        id=conversation_id,
        messages=[],
        created_at="2026-05-06T00:00:00Z",
    )
