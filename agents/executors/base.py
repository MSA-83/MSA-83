"""Base executor for task-specific agents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExecutorStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    status: ExecutorStatus
    output: str = ""
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseExecutor(ABC):
    """Base class for task executors."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = ExecutorStatus.PENDING

    @abstractmethod
    async def execute(self, task_input: str, context: dict | None = None) -> TaskResult:
        """Execute the task and return result."""
        pass

    @abstractmethod
    def validate_input(self, task_input: str) -> bool:
        """Validate task input before execution."""
        pass

    async def run(self, task_input: str, context: dict | None = None) -> TaskResult:
        """Run executor with validation."""
        if not self.validate_input(task_input):
            return TaskResult(
                status=ExecutorStatus.FAILED,
                error="Invalid input for this executor",
            )

        self.status = ExecutorStatus.RUNNING

        try:
            result = await self.execute(task_input, context)
            self.status = result.status
            return result
        except Exception as e:
            self.status = ExecutorStatus.FAILED
            return TaskResult(
                status=ExecutorStatus.FAILED,
                error=str(e),
            )

    def cancel(self) -> TaskResult:
        """Cancel the current task."""
        self.status = ExecutorStatus.CANCELLED
        return TaskResult(status=ExecutorStatus.CANCELLED, output="Task cancelled")
