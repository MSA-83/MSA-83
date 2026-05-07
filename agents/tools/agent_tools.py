"""Custom tools for Titanium agents."""

import os
import subprocess

from agents.orchestrator.config import AgentConfig


class FileReadTool:
    """Tool for reading files."""

    name = "file_reader"
    description = "Read the contents of a file from the filesystem"

    def __init__(self, base_path: str = "/workspace"):
        self.base_path = base_path

    def run(self, file_path: str) -> str:
        full_path = os.path.join(self.base_path, file_path)

        if not os.path.exists(full_path):
            return f"Error: File not found: {full_path}"

        if not full_path.startswith(self.base_path):
            return "Error: Access denied - path outside workspace"

        try:
            with open(full_path) as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"


class FileWriteTool:
    """Tool for writing files."""

    name = "file_writer"
    description = "Write content to a file"

    def __init__(self, base_path: str = "/workspace"):
        self.base_path = base_path

    def run(self, file_path: str, content: str) -> str:
        full_path = os.path.join(self.base_path, file_path)

        if not full_path.startswith(self.base_path):
            return "Error: Access denied - path outside workspace"

        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"


class ShellTool:
    """Tool for executing shell commands (sandboxed)."""

    name = "shell_executor"
    description = "Execute a shell command in a sandboxed environment"

    ALLOWED_COMMANDS = ["ls", "cat", "grep", "find", "wc", "head", "tail", "pwd", "df", "du"]

    def run(self, command: str, timeout: int | None = None) -> str:
        timeout = timeout or AgentConfig.TOOL_TIMEOUT
        parts = command.split()

        if not parts:
            return "Error: Empty command"

        if parts[0] not in self.ALLOWED_COMMANDS:
            return f"Error: Command '{parts[0]}' not allowed. Allowed: {self.ALLOWED_COMMANDS}"

        try:
            result = subprocess.run(
                parts,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode != 0:
                return f"Command failed:\n{result.stderr}"

            return result.stdout

        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout}s"
        except Exception as e:
            return f"Error executing command: {str(e)}"


class RAGSearchTool:
    """Tool for searching the RAG memory system."""

    name = "rag_search"
    description = "Search the Titanium memory system for relevant context"

    def __init__(self):
        self._pipeline = None

    def _get_pipeline(self):
        if self._pipeline is None:
            from memory.pipelines.rag_pipeline import create_rag_pipeline

            self._pipeline = create_rag_pipeline()
        return self._pipeline

    def run(self, query: str, top_k: int = 5) -> str:
        import asyncio

        pipeline = self._get_pipeline()
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(pipeline.retrieve(query, top_k=top_k))
        loop.close()

        if not result.chunks:
            return "No relevant context found in memory."

        context = "\n\n".join(f"[{c['rank']}] (score: {c['score']:.3f})\n{c['text']}" for c in result.chunks)

        return f"Found {result.total_results} relevant passages:\n\n{context}"


class CodeExecutorTool:
    """Tool for executing code snippets safely."""

    name = "code_executor"
    description = "Execute Python code in a sandboxed environment"

    def run(self, code: str, timeout: int = 10) -> str:
        try:
            result = subprocess.run(
                ["python", "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            output = []
            if result.stdout:
                output.append(f"Output:\n{result.stdout}")
            if result.stderr:
                output.append(f"Errors:\n{result.stderr}")

            if result.returncode != 0:
                return f"Execution failed (exit code {result.returncode})\n" + "\n".join(output)

            return "\n".join(output) if output else "Code executed successfully (no output)"

        except subprocess.TimeoutExpired:
            return f"Error: Code execution timed out after {timeout}s"
        except Exception as e:
            return f"Error executing code: {str(e)}"


def get_agent_tools(agent_type: str) -> list:
    """Get the appropriate tools for an agent type."""
    tool_sets = {
        "researcher": [RAGSearchTool(), FileReadTool(), ShellTool()],
        "coder": [FileReadTool(), FileWriteTool(), CodeExecutorTool(), ShellTool()],
        "analyst": [RAGSearchTool(), CodeExecutorTool(), FileReadTool()],
        "security": [RAGSearchTool(), FileReadTool(), ShellTool()],
        "writer": [RAGSearchTool(), FileReadTool(), FileWriteTool()],
    }

    return tool_sets.get(agent_type, [RAGSearchTool()])
