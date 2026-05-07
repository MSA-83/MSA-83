"""Task-specific agent executors."""

from agents.executors.base import BaseExecutor, ExecutorStatus, TaskResult
from agents.executors.code_executor import CodeExecutor, code_executor
from agents.executors.research_executor import ResearchExecutor, research_executor
from agents.executors.security_executor import SecurityAuditExecutor, security_audit_executor
from agents.executors.summarizer_executor import SummarizerExecutor, summarizer_executor
from agents.executors.writing_executor import WritingExecutor, writing_executor

EXECUTORS = {
    "code": code_executor,
    "research": research_executor,
    "security": security_audit_executor,
    "summarizer": summarizer_executor,
    "writing": writing_executor,
}

__all__ = [
    "BaseExecutor",
    "ExecutorStatus",
    "TaskResult",
    "CodeExecutor",
    "code_executor",
    "ResearchExecutor",
    "research_executor",
    "SecurityAuditExecutor",
    "security_audit_executor",
    "SummarizerExecutor",
    "summarizer_executor",
    "WritingExecutor",
    "writing_executor",
    "EXECUTORS",
]
