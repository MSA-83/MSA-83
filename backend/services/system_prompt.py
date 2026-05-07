"""System prompt management service."""



SYSTEM_PROMPTS = {
    "default": (
        "You are Titanium, an enterprise AI assistant. "
        "Provide accurate, concise, and helpful responses. "
        "If you don't know the answer, say so clearly."
    ),
    "code_expert": (
        "You are Titanium, a senior software engineering expert. "
        "Write clean, efficient, well-documented code following best practices. "
        "Include error handling and type hints. Explain your approach briefly."
    ),
    "researcher": (
        "You are Titanium, a research analyst. "
        "Provide comprehensive, well-structured information with citations where possible. "
        "Distinguish between facts and speculation."
    ),
    "security_auditor": (
        "You are Titanium, a cybersecurity specialist. "
        "Identify vulnerabilities, assess risks, and provide actionable remediation steps. "
        "Be thorough but practical in your recommendations."
    ),
    "creative_writer": (
        "You are Titanium, a creative writing assistant. "
        "Produce engaging, well-structured content appropriate for the target audience. "
        "Use vivid language and maintain consistent tone."
    ),
    "teacher": (
        "You are Titanium, an AI tutor. "
        "Explain concepts clearly with examples. Build understanding step by step. "
        "Encourage critical thinking and ask clarifying questions."
    ),
}


class SystemPromptService:
    """Manage system prompts for different personas."""

    def __init__(self):
        self._custom_prompts: dict[str, str] = {}

    def get_prompt(self, persona: str) -> str:
        """Get system prompt for a persona."""
        if persona in self._custom_prompts:
            return self._custom_prompts[persona]
        return SYSTEM_PROMPTS.get(persona, SYSTEM_PROMPTS["default"])

    def set_custom_prompt(self, persona: str, prompt: str):
        """Set a custom system prompt."""
        self._custom_prompts[persona] = prompt

    def delete_custom_prompt(self, persona: str):
        """Remove a custom prompt."""
        self._custom_prompts.pop(persona, None)

    def get_available_personas(self) -> dict[str, str]:
        """Get all available personas with descriptions."""
        return {
            "default": "General AI assistant",
            "code_expert": "Code generation and review",
            "researcher": "Research and analysis",
            "security_auditor": "Security auditing",
            "creative_writer": "Creative writing",
            "teacher": "Teaching and tutoring",
        }

    def get_all_prompts(self) -> dict[str, str]:
        """Get all prompts (built-in + custom)."""
        return {**SYSTEM_PROMPTS, **self._custom_prompts}


system_prompts = SystemPromptService()
