"""Research executor agent."""

from agents.executors.base import BaseExecutor, ExecutorStatus, TaskResult
from agents.tools.agent_tools import URLFetcherTool, WebSearchTool
from backend.services.ollama_service import ollama_service
from backend.services.rag_service import RAGService


class ResearchExecutor(BaseExecutor):
    """Execute research and analysis tasks."""

    def __init__(self):
        super().__init__(
            name="research_executor",
            description="Research topics, analyze data, and provide comprehensive answers",
        )
        self.web_search = WebSearchTool()
        self.url_fetcher = URLFetcherTool()

    def validate_input(self, task_input: str) -> bool:
        return bool(task_input.strip()) and len(task_input) <= 3000

    async def execute(
        self,
        task_input: str,
        context: dict | None = None,
    ) -> TaskResult:
        rag_service = RAGService()

        memory_context = ""
        memory_chunks = 0
        try:
            retrieval = await rag_service.retrieve_context(task_input, top_k=5)
            if retrieval and retrieval.get("chunks"):
                memory_chunks = len(retrieval["chunks"])
                memory_context = "\n\n".join(c.get("text", "") for c in retrieval["chunks"][:3])
        except Exception:
            pass

        web_context = ""
        web_results_count = 0
        if not memory_context or (context and context.get("use_web_search", True)):
            try:
                search_results = self.web_search.run(task_input)
                if "No web search results" not in search_results:
                    web_results_count = search_results.count("[") - 1
                    web_context = f"\n\nWeb search results:\n{search_results[:2000]}"

                    url_pattern = __import__("re").compile(r"URL: (https?://\S+)")
                    urls = url_pattern.findall(search_results)
                    for url in urls[:2]:
                        try:
                            fetched = self.url_fetcher.run(url)
                            if not fetched.startswith("Error"):
                                web_context += f"\n\nContent from {url}:\n{fetched[20:500]}"
                        except Exception:
                            pass
            except Exception:
                pass

        system_prompt = (
            "You are a research analyst. Provide comprehensive, well-structured information. "
            "Distinguish between facts and speculation. "
            "Cite sources when possible."
        )

        context_parts = []
        if memory_context:
            context_parts.append(f"Relevant context from internal memory:\n\n{memory_context}")
        if web_context:
            context_parts.append(f"External research:{web_context}")

        user_content = task_input
        if context_parts:
            user_content = "\n\n---\n\n".join(context_parts) + f"\n\n---\n\nQuestion: {task_input}"

        response = await ollama_service.chat(
            model="llama3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )

        output = response.get("message", {}).get("content", "")

        sources = []
        if memory_context:
            sources.append("internal_memory")
        if web_context:
            sources.append("web_search")

        return TaskResult(
            status=ExecutorStatus.COMPLETED,
            output=output,
            metadata={
                "used_memory": bool(memory_context),
                "memory_chunks": memory_chunks,
                "used_web_search": bool(web_context),
                "web_results": web_results_count,
                "sources": sources,
                "token_count": len(output.split()),
            },
        )


research_executor = ResearchExecutor()
