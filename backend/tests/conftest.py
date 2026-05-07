"""Shared test configuration."""

import pytest


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    import os

    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing"
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
    os.environ["EMBEDDER_PROVIDER"] = "ollama"
    os.environ["VECTOR_STORE"] = "memory"
