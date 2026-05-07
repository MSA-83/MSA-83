"""Input validation and sanitization utilities."""

import html
import re
from typing import Any

MAX_INPUT_LENGTH = 10000
MAX_FILENAME_LENGTH = 255
ALLOWED_FILE_TYPES = {
    ".pdf",
    ".docx",
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".yml",
    ".yaml",
    ".xml",
    ".toml",
    ".ini",
    ".cfg",
}

DANGEROUS_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
PATH_TRAVERSAL = re.compile(r"(\.\./|\.\.\\|%2e%2e|%252e%252e)")
SQL_INJECTION = re.compile(
    r"(?i)(union\s+select|drop\s+table|;\s*drop|'\s*or\s+'1'\s*=\s*'1|"
    r"'\s*or\s+1\s*=\s*1|--\s*$|/\*.*\*/)"
)
XSS_PATTERNS = re.compile(r"(?i)(<script|javascript:|on\w+\s*=|vbscript:|data:text/html)")


class InputValidator:
    """Validate and sanitize user inputs."""

    @staticmethod
    def validate_string(value: str, max_length: int = MAX_INPUT_LENGTH) -> str:
        """Validate and clean a string input."""
        if not isinstance(value, str):
            raise ValueError("Input must be a string")

        if len(value) > max_length:
            raise ValueError(f"Input exceeds maximum length of {max_length}")

        if DANGEROUS_CHARACTERS.search(value):
            raise ValueError("Input contains invalid control characters")

        return value.strip()

    @staticmethod
    def validate_filename(filename: str) -> str:
        """Validate uploaded filename."""
        if not isinstance(filename, str):
            raise ValueError("Filename must be a string")

        if len(filename) > MAX_FILENAME_LENGTH:
            raise ValueError(f"Filename exceeds maximum length of {MAX_FILENAME_LENGTH}")

        if PATH_TRAVERSAL.search(filename):
            raise ValueError("Path traversal detected in filename")

        import os

        basename = os.path.basename(filename)
        if basename != filename:
            raise ValueError("Filename contains path separators")

        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_FILE_TYPES:
            raise ValueError(f"File type '{ext}' not allowed")

        return basename

    @staticmethod
    def validate_json(data: Any, max_depth: int = 5) -> dict:
        """Validate JSON input structure."""
        if not isinstance(data, dict):
            raise ValueError("Input must be a JSON object")

        def check_depth(obj: Any, depth: int) -> None:
            if depth > max_depth:
                raise ValueError(f"JSON nesting exceeds maximum depth of {max_depth}")
            if isinstance(obj, dict):
                for v in obj.values():
                    check_depth(v, depth + 1)
            elif isinstance(obj, (list, tuple)):
                for item in obj:
                    check_depth(item, depth + 1)

        check_depth(data, 0)
        return data

    @staticmethod
    def sanitize_html(text: str) -> str:
        """Escape HTML to prevent XSS."""
        return html.escape(text, quote=True)

    @staticmethod
    def check_sql_injection(text: str) -> bool:
        """Check for SQL injection patterns."""
        return bool(SQL_INJECTION.search(text))

    @staticmethod
    def check_xss(text: str) -> bool:
        """Check for XSS patterns."""
        return bool(XSS_PATTERNS.search(text))

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format."""
        cleaned = email.strip().lower()
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, cleaned):
            raise ValueError("Invalid email format")
        return cleaned

    @staticmethod
    def validate_pagination(page: int, page_size: int) -> tuple[int, int]:
        """Validate pagination parameters."""
        page = max(1, min(page, 1000))
        page_size = max(1, min(page_size, 100))
        return page, page_size


validator = InputValidator()
