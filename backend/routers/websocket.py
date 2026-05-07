"""WebSocket router for real-time chat streaming."""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.security.input_validation import validator as input_validator
from backend.security.prompt_injection import detector as injection_detector
from backend.services.ollama_service import OllamaService
from backend.services.rag_service import RAGService

router = APIRouter()

ollama_service = OllamaService()
rag_service = RAGService()


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(message))

    async def broadcast(self, message: dict, exclude: str | None = None):
        for client_id, websocket in self.active_connections.items():
            if client_id != exclude:
                await websocket.send_text(json.dumps(message))


manager = ConnectionManager()


@router.websocket("/ws/chat/{client_id}")
async def websocket_chat(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time chat streaming."""
    await manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            message = message_data.get("message", "")
            use_rag = message_data.get("use_rag", True)
            model = message_data.get("model")
            temperature = message_data.get("temperature", 0.7)

            if not message:
                await manager.send_message(
                    client_id,
                    {
                        "type": "error",
                        "content": "Empty message",
                    },
                )
                continue

            input_validator.validate_string(message)

            injection_result = injection_detector.analyze(message)
            if injection_result["is_suspicious"] and injection_result["max_severity"] in ("HIGH", "CRITICAL"):
                await manager.send_message(
                    client_id,
                    {
                        "type": "error",
                        "content": "Potentially harmful input detected",
                    },
                )
                continue

            await manager.send_message(
                client_id,
                {
                    "type": "status",
                    "content": "Thinking...",
                },
            )

            context = None
            if use_rag:
                context_result = await rag_service.retrieve_context(message)
                if context_result:
                    context = context_result["context_text"]

            full_response = ""

            async for chunk in ollama_service.generate_stream(
                prompt=message,
                context=context,
                model=model,
                temperature=temperature,
            ):
                try:
                    chunk_data = json.loads(chunk)
                    token = chunk_data.get("chunk", "")
                    full_response += token

                    await manager.send_message(
                        client_id,
                        {
                            "type": "chunk",
                            "content": token,
                        },
                    )
                except json.JSONDecodeError:
                    continue

            await manager.send_message(
                client_id,
                {
                    "type": "done",
                    "content": full_response,
                },
            )

    except WebSocketDisconnect:
        manager.disconnect(client_id)


@router.websocket("/ws/agents/{client_id}")
async def websocket_agents(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time agent task updates."""
    await manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()
            task_data = json.loads(data)

            task = task_data.get("task", "")
            agent_type = task_data.get("agent_type", "general")

            await manager.send_message(
                client_id,
                {
                    "type": "status",
                    "content": f"Assigning to {agent_type} agent...",
                },
            )

            from backend.services.agent_orchestrator import AgentOrchestrator

            orchestrator = AgentOrchestrator()
            result = await orchestrator.execute_task(
                task=task,
                agent_type=agent_type,
            )

            await manager.send_message(
                client_id,
                {
                    "type": "result",
                    "task_id": result.get("task_id"),
                    "content": result.get("result", ""),
                    "status": result.get("status"),
                },
            )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
