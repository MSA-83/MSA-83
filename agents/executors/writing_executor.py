"""Writing executor agent."""


from agents.executors.base import BaseExecutor, ExecutorStatus, TaskResult
from backend.services.ollama_service import ollama_service

WRITING_STYLES = {
    "professional": "Write in a formal, professional tone suitable for business communication.",
    "casual": "Write in a friendly, conversational tone.",
    "technical": "Write with technical precision, using appropriate terminology.",
    "creative": "Write with vivid language, creative metaphors, and engaging prose.",
    "academic": "Write in an academic style with formal structure and citations.",
    "marketing": "Write persuasive, benefit-focused copy optimized for conversion.",
}


class WritingExecutor(BaseExecutor):
    """Execute writing and content generation tasks."""

    def __init__(self):
        super().__init__(
            name="writing_executor",
            description="Generate and refine written content",
        )

    def validate_input(self, task_input: str) -> bool:
        return bool(task_input.strip()) and len(task_input) <= 5000

    async def execute(
        self,
        task_input: str,
        context: dict | None = None,
    ) -> TaskResult:
        style = context.get("style", "professional") if context else "professional"
        style_prompt = WRITING_STYLES.get(style, WRITING_STYLES["professional"])

        system_prompt = (
            f"You are a creative writing assistant. {style_prompt} "
            "Produce well-structured content appropriate for the target audience. "
            "Maintain consistent tone throughout."
        )

        word_count = context.get("word_count", None) if context else None
        if word_count:
            task_input += f"\n\nTarget word count: approximately {word_count} words."

        response = await ollama_service.chat(
            model="llama3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task_input},
            ],
        )

        output = response.get("message", {}).get("content", "")
        word_count_actual = len(output.split())

        return TaskResult(
            status=ExecutorStatus.COMPLETED,
            output=output,
            metadata={
                "style": style,
                "word_count": word_count_actual,
                "paragraph_count": output.count("\n\n") + 1,
                "token_count": word_count_actual,
            },
        )


writing_executor = WritingExecutor()
