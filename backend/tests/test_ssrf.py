"""Tests for SSRF protection."""

from backend.security.ssrf import SSRFProtector


class TestSSRFProtector:
    """Test SSRF protection."""

    def setup_method(self):
        self.protector = SSRFProtector()
        self.protector_allow = SSRFProtector(allow_private=True)

    def test_valid_public_url(self):
        """Should allow valid public URLs."""
        assert self.protector.validate_url("https://example.com/api/data") is True
        assert self.protector.validate_url("http://api.example.com/v1") is True

    def test_localhost_blocked(self):
        """Should block localhost URLs."""
        assert self.protector.validate_url("http://localhost:8080/admin") is False
        assert self.protector.validate_url("http://127.0.0.1:8000/api") is False

    def test_private_ip_blocked(self):
        """Should block private IP addresses."""
        assert self.protector.validate_url("http://192.168.1.1/admin") is False
        assert self.protector.validate_url("http://10.0.0.1/internal") is False
        assert self.protector.validate_url("http://172.16.0.1/api") is False

    def test_metadata_endpoint_blocked(self):
        """Should block cloud metadata endpoints."""
        assert self.protector.validate_url("http://169.254.169.254/latest/meta-data/") is False
        assert self.protector.validate_url("http://metadata.google.internal/computeMetadata") is False

    def test_dangerous_schemes_blocked(self):
        """Should block dangerous URL schemes."""
        assert self.protector.validate_url("file:///etc/passwd") is False
        assert self.protector.validate_url("gopher://evil.com:1337") is False
        assert self.protector.validate_url("dict://evil.com/cmd") is False
        assert self.protector.validate_url("ftp://evil.com/file") is False
        assert self.protector.validate_url("data:text/html,<script>alert(1)</script>") is False

    def test_dns_rebinding_blocked(self):
        """Should block DNS rebinding domains."""
        assert self.protector.validate_url("http://127.0.0.1.nip.io/api") is False
        assert self.protector.validate_url("http://localhost.sslip.io/admin") is False

    def test_allow_private_when_configured(self):
        """Should allow private URLs when configured."""
        assert self.protector_allow.validate_url("http://192.168.1.1/internal") is True
        assert self.protector_allow.validate_url("http://10.0.0.1/api") is True

    def test_dangerous_schemes_still_blocked_when_private_allowed(self):
        """Should still block dangerous schemes even when private is allowed."""
        assert self.protector_allow.validate_url("file:///etc/passwd") is False
        assert self.protector_allow.validate_url("gopher://evil.com") is False

    def test_invalid_url(self):
        """Should reject malformed URLs."""
        assert self.protector.validate_url("not-a-url") is False
        assert self.protector.validate_url("") is False

    def test_missing_hostname(self):
        """Should reject URLs without hostname."""
        assert self.protector.validate_url("file:///etc/passwd") is False

    def test_blocked_host_subdomains(self):
        """Should block subdomains of blocked hosts."""
        assert self.protector.validate_url("http://evil.localhost/api") is False
        assert self.protector.validate_url("http://fake.127.0.0.1.com/api") is False

    def test_validate_multiple_urls(self):
        """Should validate multiple URLs."""
        urls = [
            "https://example.com",
            "http://localhost:8080",
            "http://192.168.1.1",
        ]
        results = self.protector.validate_urls(urls)
        assert results["https://example.com"] is True
        assert results["http://localhost:8080"] is False
        assert results["http://192.168.1.1"] is False

    def test_safe_fetch_urls_filters(self):
        """Should filter to only safe URLs."""
        urls = [
            "https://example.com",
            "http://localhost:8080",
            "https://api.github.com",
            "http://10.0.0.1",
        ]
        safe = self.protector.safe_fetch_urls(urls)
        assert len(safe) == 2
        assert "https://example.com" in safe
        assert "https://api.github.com" in safe
