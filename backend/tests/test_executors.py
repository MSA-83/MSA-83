"""Tests for agent executors."""


from agents.executors.base import BaseExecutor, ExecutorStatus
from agents.executors.code_executor import CodeExecutor
from agents.executors.research_executor import ResearchExecutor
from agents.executors.security_executor import SecurityAuditExecutor
from agents.executors.writing_executor import WritingExecutor


class TestBaseExecutor:
    """Test base executor functionality."""

    def test_executor_initial_status(self):
        """Executor should start in PENDING status."""
        executor = CodeExecutor()
        assert executor.status == ExecutorStatus.PENDING

    def test_executor_name_and_description(self):
        """Executor should have name and description."""
        executor = CodeExecutor()
        assert executor.name == "code_executor"
        assert executor.description == "Generate, review, and explain code"

    def test_cancel_task(self):
        """Should be able to cancel a task."""
        executor = CodeExecutor()
        result = executor.cancel()
        assert result.status == ExecutorStatus.CANCELLED
        assert executor.status == ExecutorStatus.CANCELLED


class TestCodeExecutor:
    """Test code executor."""

    def setup_method(self):
        self.executor = CodeExecutor()

    def test_validate_input_valid(self):
        """Should accept valid code input."""
        assert self.executor.validate_input("Write a Python function to sort a list") is True

    def test_validate_input_empty(self):
        """Should reject empty input."""
        assert self.executor.validate_input("") is False
        assert self.executor.validate_input("   ") is False

    def test_validate_input_too_long(self):
        """Should reject input exceeding max length."""
        long_input = "a" * 5001
        assert self.executor.validate_input(long_input) is False

    def test_detect_python(self):
        """Should detect Python code blocks."""
        output = "Here is the code:\n```python\ndef hello():\n    pass\n```"
        assert self.executor._detect_language(output) == "python"

    def test_detect_javascript(self):
        """Should detect JavaScript code blocks."""
        output = "Here is the code:\n```javascript\nconst x = 1;\n```"
        assert self.executor._detect_language(output) == "javascript"

    def test_detect_typescript(self):
        """Should detect TypeScript code blocks."""
        output = "```typescript\nconst x: number = 1;\n```"
        assert self.executor._detect_language(output) == "typescript"

    def test_detect_bash(self):
        """Should detect Bash code blocks."""
        output = "```bash\necho hello\n```"
        assert self.executor._detect_language(output) == "bash"

    def test_detect_unknown(self):
        """Should return unknown for no code blocks."""
        output = "This is just text without code."
        assert self.executor._detect_language(output) == "unknown"

    def test_extract_code_single_block(self):
        """Should extract single code block."""
        output = "```python\ndef test():\n    return True\n```"
        blocks = self.executor._extract_code(output)
        assert len(blocks) == 1
        assert blocks[0]["language"] == "python"
        assert "def test()" in blocks[0]["code"]

    def test_extract_code_multiple_blocks(self):
        """Should extract multiple code blocks."""
        output = """```python
def hello():
    pass
```

Some text

```javascript
const x = 1;
```"""
        blocks = self.executor._extract_code(output)
        assert len(blocks) == 2

    def test_extract_code_no_blocks(self):
        """Should return empty list when no code blocks."""
        output = "No code here."
        blocks = self.executor._extract_code(output)
        assert len(blocks) == 0


class TestResearchExecutor:
    """Test research executor."""

    def setup_method(self):
        self.executor = ResearchExecutor()

    def test_validate_input_valid(self):
        """Should accept valid research input."""
        assert self.executor.validate_input("Explain quantum computing") is True

    def test_validate_input_empty(self):
        """Should reject empty input."""
        assert self.executor.validate_input("") is False

    def test_validate_input_too_long(self):
        """Should reject input exceeding max length."""
        long_input = "a" * 3001
        assert self.executor.validate_input(long_input) is False


class TestSecurityAuditExecutor:
    """Test security audit executor."""

    def setup_method(self):
        self.executor = SecurityAuditExecutor()

    def test_validate_input_valid(self):
        """Should accept valid audit input."""
        assert self.executor.validate_input("Audit this code for vulnerabilities") is True

    def test_validate_input_empty(self):
        """Should reject empty input."""
        assert self.executor.validate_input("") is False

    def test_validate_input_max_length(self):
        """Should accept up to max length."""
        max_input = "a" * 10000
        assert self.executor.validate_input(max_input) is True

    def test_validate_input_exceeds_max(self):
        """Should reject input exceeding max length."""
        long_input = "a" * 10001
        assert self.executor.validate_input(long_input) is False

    def test_parse_findings_detects_categories(self):
        """Should parse vulnerability categories from output."""
        output = "Found SQL Injection and Cross-Site Scripting (XSS) vulnerabilities."
        findings = self.executor._parse_findings(output)
        assert len(findings) == 2
        assert any(f["category"] == "SQL Injection" for f in findings)
        assert any(f["category"] == "Cross-Site Scripting (XSS)" for f in findings)

    def test_parse_findings_empty(self):
        """Should return empty list when no categories found."""
        output = "No vulnerabilities found."
        findings = self.executor._parse_findings(output)
        assert len(findings) == 0


class TestWritingExecutor:
    """Test writing executor."""

    def setup_method(self):
        self.executor = WritingExecutor()

    def test_validate_input_valid(self):
        """Should accept valid writing input."""
        assert self.executor.validate_input("Write a blog post about AI") is True

    def test_validate_input_empty(self):
        """Should reject empty input."""
        assert self.executor.validate_input("") is False

    def test_validate_input_too_long(self):
        """Should reject input exceeding max length."""
        long_input = "a" * 5001
        assert self.executor.validate_input(long_input) is False


class TestExecutorRegistry:
    """Test executor registry."""

    def test_all_executors_registered(self):
        """All executors should be in the registry."""
        from agents.executors import EXECUTORS

        assert "code" in EXECUTORS
        assert "research" in EXECUTORS
        assert "security" in EXECUTORS
        assert "writing" in EXECUTORS

    def test_all_executors_are_instances(self):
        """All registered executors should be BaseExecutor instances."""
        from agents.executors import EXECUTORS

        for name, executor in EXECUTORS.items():
            assert isinstance(executor, BaseExecutor)

    def test_executor_names_match(self):
        """Executor names should match registry keys."""
        from agents.executors import EXECUTORS

        for key, executor in EXECUTORS.items():
            assert key in executor.name
