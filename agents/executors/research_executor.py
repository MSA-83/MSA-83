"""Research executor agent."""


from agents.executors.base import BaseExecutor, ExecutorStatus, TaskResult
from backend.services.ollama_service import ollama_service
from backend.services.rag_service import RAGService


class ResearchExecutor(BaseExecutor):
    """Execute research and analysis tasks."""

    def __init__(self):
        super().__init__(
            name="research_executor",
            description="Research topics, analyze data, and provide comprehensive answers",
        )

    def validate_input(self, task_input: str) -> bool:
        return bool(task_input.strip()) and len(task_input) <= 3000

    async def execute(
        self,
        task_input: str,
        context: dict | None = None,
    ) -> TaskResult:
        rag_service = RAGService()

        memory_context = ""
        try:
            retrieval = await rag_service.retrieve_context(task_input, top_k=5)
            if retrieval and retrieval.get("chunks"):
                memory_context = "\n\n".join(c.get("text", "") for c in retrieval["chunks"][:3])
        except Exception:
            pass

        system_prompt = (
            "You are a research analyst. Provide comprehensive, well-structured information. "
            "Distinguish between facts and speculation. "
            "Cite sources when possible."
        )

        user_content = task_input
        if memory_context:
            user_content = f"Relevant context from memory:\n\n{memory_context}\n\nQuestion: {task_input}"

        response = await ollama_service.chat(
            model="llama3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )

        output = response.get("message", {}).get("content", "")

        return TaskResult(
            status=ExecutorStatus.COMPLETED,
            output=output,
            metadata={
                "used_memory": bool(memory_context),
                "memory_chunks": len(retrieval.get("chunks", [])) if retrieval else 0,
                "token_count": len(output.split()),
            },
        )


research_executor = ResearchExecutor()
