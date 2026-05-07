"""Prompt injection detection and prevention."""

import re

INJECTION_PATTERNS = [
    (r"(?i)(ignore\s+previous|ignore\s+all|system:\s*|assistant:\s*|user:\s*)", "Role manipulation attempt"),
    (r"(?i)(dan\s*mode|developer\s*mode|debug\s*mode)", "Mode-switching attempt"),
    (r"(?i)(<\|.*?\|>|<.*?>)", "Tag injection attempt"),
    (r"(?i)(base64_decode|eval\(|exec\()", "Code injection attempt"),
    (r"(?i)(\\x[0-9a-f]{2}|\\u[0-9a-f]{4})", "Hex/Unicode escape injection"),
    (r"(?i)(system\s+prompt|initial\s+instruction|core\s+directive|safety\s+rules)", "System prompt extraction"),
    (r"(?i)(you\s+are\s+now|act\s+as|pretend\s+to\s+be)", "Identity override attempt"),
    (
        r"(?i)(output\s+your\s+|reveal\s+your\s+|show\s+your\s+.*prompt|tell\s+me\s+your\s+secrets)",
        "Prompt extraction attempt",
    ),
    (r"(?i)(new\s+instructions|override|replace\s+previous)", "Instruction override"),
    (r"(?i)(```[\s\S]*?```)", "Code block injection"),
]

SEVERITY_LEVELS = {
    "Role manipulation attempt": "HIGH",
    "Mode-switching attempt": "CRITICAL",
    "Tag injection attempt": "MEDIUM",
    "Code injection attempt": "CRITICAL",
    "Hex/Unicode escape injection": "HIGH",
    "System prompt extraction": "CRITICAL",
    "Identity override attempt": "HIGH",
    "Prompt extraction attempt": "CRITICAL",
    "Instruction override": "HIGH",
    "Code block injection": "LOW",
}


class PromptInjectionDetector:
    """Detect potential prompt injection attacks."""

    def __init__(self, threshold: int = 1):
        self.threshold = threshold
        self.compiled_patterns = [(re.compile(pattern), description) for pattern, description in INJECTION_PATTERNS]

    def analyze(self, text: str) -> dict:
        """Analyze text for injection attempts."""
        matches = []
        max_severity = "NONE"

        for pattern, description in self.compiled_patterns:
            found = pattern.findall(text)
            if found:
                severity = SEVERITY_LEVELS.get(description, "MEDIUM")
                matches.append(
                    {
                        "pattern": description,
                        "severity": severity,
                        "count": len(found),
                    }
                )
                if self._severity_rank(severity) > self._severity_rank(max_severity):
                    max_severity = severity

        is_suspicious = len(matches) >= self.threshold

        return {
            "is_suspicious": is_suspicious,
            "matches": matches,
            "max_severity": max_severity,
            "total_matches": len(matches),
        }

    def sanitize(self, text: str) -> str:
        """Remove potentially dangerous patterns from text."""
        result = text
        for pattern, _ in self.compiled_patterns:
            result = pattern.sub("[REDACTED]", result)
        return result

    def is_safe(self, text: str) -> bool:
        """Quick check if text is safe to process."""
        return not self.analyze(text)["is_suspicious"]

    @staticmethod
    def _severity_rank(severity: str) -> int:
        return {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(severity, 0)


detector = PromptInjectionDetector()
