"""Tests for system prompt service."""

from backend.services.system_prompt import SYSTEM_PROMPTS, system_prompts


class TestSystemPromptService:
    """Test system prompt management."""

    def test_default_prompt_exists(self):
        """Default prompt should exist."""
        assert "default" in SYSTEM_PROMPTS
        assert len(SYSTEM_PROMPTS["default"]) > 0

    def test_all_personas_have_prompts(self):
        """All built-in personas should have prompts."""
        for persona in ["default", "code_expert", "researcher", "security_auditor", "creative_writer", "teacher"]:
            assert persona in SYSTEM_PROMPTS
            assert len(SYSTEM_PROMPTS[persona]) > 0

    def test_get_builtin_prompt(self):
        """Should return built-in prompt."""
        prompt = system_prompts.get_prompt("code_expert")
        assert "engineer" in prompt.lower() or "code" in prompt.lower()

    def test_get_unknown_prompt_returns_default(self):
        """Should return default for unknown persona."""
        prompt = system_prompts.get_prompt("nonexistent")
        assert prompt == SYSTEM_PROMPTS["default"]

    def test_set_custom_prompt(self):
        """Should allow setting custom prompts."""
        system_prompts.set_custom_prompt("custom_bot", "You are a custom bot")
        assert system_prompts.get_prompt("custom_bot") == "You are a custom bot"

    def test_custom_overrides_builtin(self):
        """Custom prompt should override built-in."""
        system_prompts.set_custom_prompt("default", "Custom default")
        assert system_prompts.get_prompt("default") == "Custom default"

    def test_delete_custom_prompt(self):
        """Should allow deleting custom prompts."""
        system_prompts.set_custom_prompt("temp", "Temporary")
        system_prompts.delete_custom_prompt("temp")
        assert system_prompts.get_prompt("temp") == SYSTEM_PROMPTS.get("temp", SYSTEM_PROMPTS["default"])

    def test_delete_nonexistent_prompt(self):
        """Should not raise when deleting nonexistent prompt."""
        system_prompts.delete_custom_prompt("does_not_exist")

    def test_get_available_personas(self):
        """Should return all available personas with descriptions."""
        personas = system_prompts.get_available_personas()
        assert isinstance(personas, dict)
        assert "default" in personas
        assert "code_expert" in personas
        assert len(personas) >= 6

    def test_get_all_prompts(self):
        """Should return all prompts including custom."""
        system_prompts.set_custom_prompt("test_custom", "Test prompt")
        all_prompts = system_prompts.get_all_prompts()
        assert "default" in all_prompts
        assert "test_custom" in all_prompts
        assert all_prompts["test_custom"] == "Test prompt"

    def test_prompts_are_strings(self):
        """All prompts should be non-empty strings."""
        for persona, prompt in SYSTEM_PROMPTS.items():
            assert isinstance(prompt, str)
            assert len(prompt) > 0
