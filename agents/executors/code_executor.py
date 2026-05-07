"""Code executor agent."""

import re

from agents.executors.base import BaseExecutor, ExecutorStatus, TaskResult
from backend.services.ollama_service import ollama_service

CODE_PATTERNS = {
    "python": r"```python\s*([\s\S]*?)```",
    "javascript": r"```(?:js|javascript)\s*([\s\S]*?)```",
    "typescript": r"```(?:ts|typescript)\s*([\s\S]*?)```",
    "bash": r"```(?:bash|sh|shell)\s*([\s\S]*?)```",
}


class CodeExecutor(BaseExecutor):
    """Execute code-related tasks."""

    def __init__(self):
        super().__init__(
            name="code_executor",
            description="Generate, review, and explain code",
        )

    def validate_input(self, task_input: str) -> bool:
        return bool(task_input.strip()) and len(task_input) <= 5000

    async def execute(
        self,
        task_input: str,
        context: dict | None = None,
    ) -> TaskResult:
        system_prompt = (
            "You are a senior software engineer. "
            "Write clean, efficient code with proper error handling. "
            "Include type hints and docstrings. Explain your approach briefly."
        )

        if context and context.get("language"):
            system_prompt += f"\nTarget language: {context['language']}"

        if context and context.get("style_guide"):
            system_prompt += f"\nStyle guide: {context['style_guide']}"

        response = await ollama_service.chat(
            model="llama3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task_input},
            ],
        )

        output = response.get("message", {}).get("content", "")

        language = self._detect_language(output)

        return TaskResult(
            status=ExecutorStatus.COMPLETED,
            output=output,
            metadata={
                "language": language,
                "has_code": bool(self._extract_code(output)),
                "token_count": len(output.split()),
            },
        )

    def _detect_language(self, output: str) -> str:
        for lang, pattern in CODE_PATTERNS.items():
            if re.search(pattern, output):
                return lang
        return "unknown"

    def _extract_code(self, output: str) -> list[dict]:
        code_blocks = []
        for lang, pattern in CODE_PATTERNS.items():
            for match in re.finditer(pattern, output):
                code_blocks.append({"language": lang, "code": match.group(1).strip()})
        return code_blocks


code_executor = CodeExecutor()
