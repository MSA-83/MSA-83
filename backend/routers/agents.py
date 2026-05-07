"""Agents router for multi-agent orchestration."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.security.input_validation import validator as input_validator
from backend.security.prompt_injection import detector as injection_detector
from backend.services.agent_orchestrator import AgentOrchestrator

router = APIRouter()
orchestrator = AgentOrchestrator()


class AgentTask(BaseModel):
    task: str
    agent_type: str = "general"
    use_memory: bool = True
    priority: str = "normal"
    metadata: dict | None = None


class AgentTaskResponse(BaseModel):
    task_id: str
    status: str
    result: str | None = None
    agent_type: str


class AgentStatus(BaseModel):
    agent_id: str
    status: str
    tasks_completed: int
    last_active: str


@router.post("/task", response_model=AgentTaskResponse)
async def create_task(request: AgentTask):
    """Create a new agent task."""
    try:
        input_validator.validate_string(request.task, max_length=10000)

        injection_result = injection_detector.analyze(request.task)
        if injection_result["is_suspicious"] and injection_result["max_severity"] in ("HIGH", "CRITICAL"):
            raise HTTPException(
                status_code=400,
                detail=f"Potential prompt injection detected: {injection_result['matches'][0]['pattern']}",
            )

        result = await orchestrator.execute_task(
            task=request.task,
            agent_type=request.agent_type,
            use_memory=request.use_memory,
            priority=request.priority,
        )

        return AgentTaskResponse(
            task_id=result["task_id"],
            status=result["status"],
            result=result.get("result"),
            agent_type=request.agent_type,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of an agent task."""
    status = await orchestrator.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status


@router.get("/status")
async def get_agents_status():
    """Get status of all agents."""
    return await orchestrator.get_all_agents_status()


@router.post("/task/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a running agent task."""
    result = await orchestrator.cancel_task(task_id)
    return result
