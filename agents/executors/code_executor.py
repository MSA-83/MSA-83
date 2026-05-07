"""Code executor agent."""

import re

from agents.executors.base import BaseExecutor, ExecutorStatus, TaskResult
from agents.tools.agent_tools import CodeAnalysisTool
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
        self.code_analyzer = CodeAnalysisTool()

    def validate_input(self, task_input: str) -> bool:
        return bool(task_input.strip()) and len(task_input) <= 5000

    async def execute(
        self,
        task_input: str,
        context: dict | None = None,
    ) -> TaskResult:
        language = context.get("language", "") if context else ""
        task_type = context.get("task_type", "generate") if context else "generate"

        if task_type == "review":
            return await self._review_code(task_input, language)
        elif task_type == "explain":
            return await self._explain_code(task_input, language)
        else:
            return await self._generate_code(task_input, language, context)

    async def _generate_code(
        self,
        task_input: str,
        language: str,
        context: dict | None = None,
    ) -> TaskResult:
        system_prompt = (
            "You are a senior software engineer. "
            "Write clean, efficient code with proper error handling. "
            "Include type hints and docstrings. Explain your approach briefly."
        )

        if language:
            system_prompt += f"\nTarget language: {language}"

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
        detected_lang = self._detect_language(output)
        code_blocks = self._extract_code(output)

        analysis_issues = 0
        if detected_lang == "python":
            code_text = "\n".join(b["code"] for b in code_blocks) if code_blocks else output
            analysis = self.code_analyzer.run(code_text)
            if not analysis.startswith("No issues") and not analysis.startswith("Syntax error"):
                analysis_issues = len([l for l in analysis.split("\n") if l.startswith("-")])

        return TaskResult(
            status=ExecutorStatus.COMPLETED,
            output=output,
            metadata={
                "language": detected_lang,
                "has_code": bool(code_blocks),
                "code_blocks": len(code_blocks),
                "analysis_issues": analysis_issues,
                "token_count": len(output.split()),
            },
        )

    async def _review_code(self, task_input: str, language: str) -> TaskResult:
        system_prompt = (
            "You are a senior code reviewer. Analyze the provided code for:\n"
            "1. Bugs and logical errors\n"
            "2. Security vulnerabilities\n"
            "3. Performance issues\n"
            "4. Code style and readability\n"
            "5. Best practices violations\n\n"
            "Provide specific line references and suggest fixes."
        )

        analysis = ""
        if language == "python":
            analysis = self.code_analyzer.run(task_input)

        user_content = f"Code to review:\n\n{task_input}"
        if analysis and not analysis.startswith("No issues"):
            user_content += f"\n\nStatic analysis findings:\n{analysis}"

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
                "language": language or "unknown",
                "task_type": "review",
                "static_analysis_issues": len([l for l in analysis.split("\n") if l.startswith("-")]) if analysis else 0,
                "token_count": len(output.split()),
            },
        )

    async def _explain_code(self, task_input: str, language: str) -> TaskResult:
        system_prompt = (
            "You are a technical educator. Explain the provided code clearly:\n"
            "1. What the code does (high-level)\n"
            "2. How it works (step by step)\n"
            "3. Key concepts and patterns used\n"
            "4. Potential improvements"
        )

        response = await ollama_service.chat(
            model="llama3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Code to explain:\n\n{task_input}"},
            ],
        )

        output = response.get("message", {}).get("content", "")

        return TaskResult(
            status=ExecutorStatus.COMPLETED,
            output=output,
            metadata={
                "language": language or "unknown",
                "task_type": "explain",
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
