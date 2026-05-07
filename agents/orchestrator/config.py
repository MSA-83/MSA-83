"""CrewAI agent base configuration for Titanium platform."""

import os


class AgentConfig:
    """Configuration for Titanium agents."""

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
    LLM_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))

    MEMORY_ENABLED = os.getenv("AGENT_MEMORY", "true").lower() == "true"
    MEMORY_TOP_K = int(os.getenv("MEMORY_TOP_K", "5"))

    TOOL_TIMEOUT = int(os.getenv("TOOL_TIMEOUT", "30"))
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "10"))

    @classmethod
    def get_llm_config(cls) -> dict:
        return {
            "provider": cls.LLM_PROVIDER,
            "model": cls.LLM_MODEL,
            "base_url": cls.LLM_BASE_URL,
            "temperature": cls.LLM_TEMPERATURE,
            "max_tokens": cls.LLM_MAX_TOKENS,
        }


AGENT_ROLES = {
    "researcher": {
        "role": "Senior Research Analyst",
        "goal": "Uncover cutting-edge developments and gather comprehensive information",
        "backstory": (
            "You are a Senior Research Analyst with expertise in information gathering, "
            "synthesis, and analysis. You excel at finding relevant, accurate information "
            "from various sources and presenting it in a clear, actionable format."
        ),
    },
    "coder": {
        "role": "Senior Software Engineer",
        "goal": "Write clean, efficient, and well-documented code",
        "backstory": (
            "You are a Senior Software Engineer with deep expertise in multiple programming "
            "languages and frameworks. You write production-quality code with proper error "
            "handling, documentation, and follow best practices."
        ),
    },
    "analyst": {
        "role": "Data Analytics Expert",
        "goal": "Extract meaningful insights from data and provide actionable recommendations",
        "backstory": (
            "You are a Data Analytics Expert skilled in statistical analysis, data visualization, "
            "and business intelligence. You transform raw data into clear insights and "
            "actionable recommendations."
        ),
    },
    "security": {
        "role": "Cybersecurity Specialist",
        "goal": "Identify vulnerabilities and recommend security improvements",
        "backstory": (
            "You are a Cybersecurity Specialist with expertise in threat analysis, "
            "vulnerability assessment, and security best practices. You identify security "
            "risks and provide actionable mitigation strategies."
        ),
    },
    "writer": {
        "role": "Content Strategist",
        "goal": "Create compelling, accurate, and well-structured content",
        "backstory": (
            "You are a Content Strategist skilled in technical writing, documentation, "
            "and communication. You produce clear, concise, and audience-appropriate content."
        ),
    },
}
