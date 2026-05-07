"""Tests for input validation."""

import pytest

from backend.security.input_validation import InputValidator


class TestInputValidator:
    """Test input validation utilities."""

    def setup_method(self):
        self.validator = InputValidator()

    def test_validate_string_valid(self):
        """Should accept valid string."""
        result = self.validator.validate_string("Hello, world!")
        assert result == "Hello, world!"

    def test_validate_string_strips_whitespace(self):
        """Should strip leading/trailing whitespace."""
        result = self.validator.validate_string("  hello  ")
        assert result == "hello"

    def test_validate_string_too_long(self):
        """Should reject strings exceeding max length."""
        long_string = "a" * 10001
        with pytest.raises(ValueError, match="exceeds maximum length"):
            self.validator.validate_string(long_string)

    def test_validate_string_custom_max_length(self):
        """Should respect custom max length."""
        with pytest.raises(ValueError):
            self.validator.validate_string("too long", max_length=5)

    def test_validate_string_not_string(self):
        """Should reject non-string input."""
        with pytest.raises(ValueError, match="must be a string"):
            self.validator.validate_string(123)

    def test_validate_string_control_characters(self):
        """Should reject control characters."""
        with pytest.raises(ValueError, match="invalid control characters"):
            self.validator.validate_string("hello\x00world")

    def test_validate_filename_valid(self):
        """Should accept valid filename."""
        result = self.validator.validate_filename("document.pdf")
        assert result == "document.pdf"

    def test_validate_filename_allowed_types(self):
        """Should accept all allowed file types."""
        for ext in [".pdf", ".docx", ".txt", ".md", ".csv", ".json", ".py"]:
            result = self.validator.validate_filename(f"test{ext}")
            assert result == f"test{ext}"

    def test_validate_filename_path_traversal(self):
        """Should reject path traversal."""
        with pytest.raises(ValueError, match="Path traversal"):
            self.validator.validate_filename("../../../etc/passwd")

    def test_validate_filename_path_separator(self):
        """Should reject path separators."""
        with pytest.raises(ValueError, match="path separators"):
            self.validator.validate_filename("folder/document.pdf")

    def test_validate_filename_too_long(self):
        """Should reject filenames exceeding max length."""
        long_name = "a" * 256 + ".txt"
        with pytest.raises(ValueError, match="exceeds maximum length"):
            self.validator.validate_filename(long_name)

    def test_validate_filename_disallowed_type(self):
        """Should reject disallowed file types."""
        with pytest.raises(ValueError, match="not allowed"):
            self.validator.validate_filename("malware.exe")

    def test_validate_json_valid(self):
        """Should accept valid JSON structure."""
        data = {"key": "value", "nested": {"a": 1}}
        result = self.validator.validate_json(data)
        assert result == data

    def test_validate_json_not_dict(self):
        """Should reject non-dict input."""
        with pytest.raises(ValueError, match="must be a JSON object"):
            self.validator.validate_json([1, 2, 3])

    def test_validate_json_max_depth(self):
        """Should reject deeply nested JSON."""
        deep = {"a": {"b": {"c": {"d": {"e": {"f": "too deep"}}}}}}
        with pytest.raises(ValueError, match="exceeds maximum depth"):
            self.validator.validate_json(deep, max_depth=3)

    def test_sanitize_html(self):
        """Should escape HTML characters."""
        result = self.validator.sanitize_html("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "<script>" not in result

    def test_sanitize_html_quotes(self):
        """Should escape quotes."""
        result = self.validator.sanitize_html('"hello"')
        assert "&quot;" in result

    def test_check_sql_injection(self):
        """Should detect SQL injection patterns."""
        assert self.validator.check_sql_injection("' OR '1'='1") is True
        assert self.validator.check_sql_injection("UNION SELECT * FROM users") is True
        assert self.validator.check_sql_injection("DROP TABLE users;") is True
        assert self.validator.check_sql_injection("SELECT * FROM users WHERE id=1") is False

    def test_check_xss(self):
        """Should detect XSS patterns."""
        assert self.validator.check_xss("<script>alert(1)</script>") is True
        assert self.validator.check_xss("javascript:void(0)") is True
        assert self.validator.check_xss("onclick=malicious()") is True
        assert self.validator.check_xss("Hello world") is False

    def test_validate_email_valid(self):
        """Should accept valid email."""
        result = self.validator.validate_email("USER@EXAMPLE.COM")
        assert result == "user@example.com"

    def test_validate_email_invalid(self):
        """Should reject invalid email."""
        with pytest.raises(ValueError, match="Invalid email"):
            self.validator.validate_email("not-an-email")

    def test_validate_email_trims_and_lowercase(self):
        """Should trim and lowercase email."""
        result = self.validator.validate_email("  Test@Example.com  ")
        assert result == "test@example.com"

    def test_validate_pagination(self):
        """Should clamp pagination values."""
        page, size = self.validator.validate_pagination(-1, 0)
        assert page == 1
        assert size == 1

        page, size = self.validator.validate_pagination(9999, 999)
        assert page == 1000
        assert size == 100

        page, size = self.validator.validate_pagination(5, 20)
        assert page == 5
        assert size == 20
