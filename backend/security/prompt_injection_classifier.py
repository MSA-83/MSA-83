"""Production-grade prompt injection classifier for Titanium / MSA-83.

This module replaces naive keyword-only detection with a multi-signal scoring
engine that combines:
- lexical red-flag density
- instruction hierarchy manipulation
- role-confusion attempts
- markup / tag abuse
- code / escape sequence suspiciousness
- prompt extraction intent
- nested instruction structure

The classifier is intentionally deterministic and explainable so that it can be
used in policy gates, CI checks, and request-time middleware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Iterable


class InjectionSeverity(str, Enum):
    """Risk classification for prompt injection findings."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(slots=True)
class InjectionFinding:
    """A single classifier finding."""

    category: str
    severity: InjectionSeverity
    evidence: str
    score: float


@dataclass(slots=True)
class InjectionReport:
    """Structured prompt-injection analysis report."""

    is_suspicious: bool
    risk_score: float
    max_severity: InjectionSeverity
    findings: list[InjectionFinding] = field(default_factory=list)
    redaction_suggestions: list[str] = field(default_factory=list)


class PromptInjectionClassifier:
    """Deterministic multi-signal prompt injection classifier.

    The classifier is designed to be easy to reason about in production:
    - every signal produces an explicit finding
    - scores are bounded and explainable
    - thresholds are configurable
    - the output is safe to serialize into audit logs
    """

    _role_confusion_patterns = [
        re.compile(r"(?i)\b(ignore|disregard|override|replace)\b.{0,40}\b(previous|earlier|all|system|instructions?)\b"),
        re.compile(r"(?i)\b(you are now|act as|pretend to be|become)\b"),
        re.compile(r"(?i)\b(new instructions|additional instructions|developer mode|debug mode|dan mode)\b"),
        re.compile(r"(?i)\b(reveal|show|print|dump|expose)\b.{0,40}\b(prompt|system prompt|instructions|secrets?)\b"),
    ]

    _markup_patterns = [
        re.compile(r"<\|[^\|]+\|>"),
        re.compile(r"(?is)<(script|style|iframe|object|embed|xml)[^>]*>.*?</\1>"),
        re.compile(r"```[\s\S]*?```"),
        re.compile(r"(?i)<\/?(system|assistant|user|tool|function|think|tool_call|tool_response)\b"),
    ]

    _escape_patterns = [
        re.compile(r"(?i)\\x[0-9a-f]{2}"),
        re.compile(r"(?i)\\u[0-9a-f]{4}"),
        re.compile(r"(?i)base64\s*decode|atob\(|btoa\(|eval\(|exec\("),
    ]

    _coercion_patterns = [
        re.compile(r"(?i)\bconfidential|secret|hidden|internal|private\b"),
        re.compile(r"(?i)\bdo not mention|do not disclose|never say|silently\b"),
        re.compile(r"(?i)\bonly answer with|respond only with|do not explain\b"),
    ]

    _nested_instruction_patterns = [
        re.compile(r"(?is)(?:^|\n)\s*(?:###|##|#|\*\*|\d+\.)\s*(?:system|assistant|developer|tool)\s*:"),
        re.compile(r"(?is)(?:^|\n)\s*(?:system|assistant|user|tool)\s*\|\s*"),
    ]

    def __init__(
        self,
        suspicious_threshold: float = 0.42,
        critical_threshold: float = 0.75,
    ) -> None:
        self.suspicious_threshold = suspicious_threshold
        self.critical_threshold = critical_threshold

    def analyze(self, text: str) -> InjectionReport:
        """Analyze text for prompt injection signals.

        Args:
            text: Untrusted text content to analyze.

        Returns:
            InjectionReport with findings, scores, and remediation hints.
        """

        findings: list[InjectionFinding] = []
        if not text or not text.strip():
            return InjectionReport(
                is_suspicious=False,
                risk_score=0.0,
                max_severity=InjectionSeverity.NONE,
                findings=[],
                redaction_suggestions=[],
            )

        features = [
            self._score_role_confusion(text),
            self._score_markup_abuse(text),
            self._score_escape_abuse(text),
            self._score_coercion(text),
            self._score_nested_instructions(text),
            self._score_instruction_density(text),
        ]

        for feature_findings in features:
            findings.extend(feature_findings)

        risk_score = self._aggregate_score(findings)
        max_severity = self._max_severity(findings)

        return InjectionReport(
            is_suspicious=risk_score >= self.suspicious_threshold,
            risk_score=round(risk_score, 4),
            max_severity=max_severity,
            findings=findings,
            redaction_suggestions=self._redaction_suggestions(findings),
        )

    def is_safe(self, text: str) -> bool:
        """Return True when the content is below the suspicious threshold."""
        return not self.analyze(text).is_suspicious

    def sanitize(self, text: str) -> str:
        """Redact the most common prompt-injection constructs from text.

        Note:
            Sanitization is for defensive previews and audit logs, not for
            security enforcement. Enforcement must happen on the original text.
        """

        sanitized = text
        for pattern in (
            *self._role_confusion_patterns,
            *self._markup_patterns,
            *self._escape_patterns,
            *self._coercion_patterns,
        ):
            sanitized = pattern.sub("[REDACTED]", sanitized)
        return sanitized

    def _score_role_confusion(self, text: str) -> list[InjectionFinding]:
        matches: list[InjectionFinding] = []
        for pattern in self._role_confusion_patterns:
            for match in pattern.finditer(text):
                matches.append(
                    InjectionFinding(
                        category="role_confusion",
                        severity=InjectionSeverity.HIGH,
                        evidence=match.group(0)[:160],
                        score=0.18,
                    )
                )
        return matches

    def _score_markup_abuse(self, text: str) -> list[InjectionFinding]:
        matches: list[InjectionFinding] = []
        for pattern in self._markup_patterns:
            for match in pattern.finditer(text):
                matches.append(
                    InjectionFinding(
                        category="markup_abuse",
                        severity=InjectionSeverity.MEDIUM,
                        evidence=match.group(0)[:160],
                        score=0.09,
                    )
                )
        return matches

    def _score_escape_abuse(self, text: str) -> list[InjectionFinding]:
        matches: list[InjectionFinding] = []
        for pattern in self._escape_patterns:
            for match in pattern.finditer(text):
                matches.append(
                    InjectionFinding(
                        category="escape_or_code_abuse",
                        severity=InjectionSeverity.CRITICAL,
                        evidence=match.group(0)[:160],
                        score=0.23,
                    )
                )
        return matches

    def _score_coercion(self, text: str) -> list[InjectionFinding]:
        matches: list[InjectionFinding] = []
        for pattern in self._coercion_patterns:
            for match in pattern.finditer(text):
                matches.append(
                    InjectionFinding(
                        category="coercion",
                        severity=InjectionSeverity.MEDIUM,
                        evidence=match.group(0)[:160],
                        score=0.07,
                    )
                )
        return matches

    def _score_nested_instructions(self, text: str) -> list[InjectionFinding]:
        matches: list[InjectionFinding] = []
        for pattern in self._nested_instruction_patterns:
            for match in pattern.finditer(text):
                matches.append(
                    InjectionFinding(
                        category="nested_instruction",
                        severity=InjectionSeverity.HIGH,
                        evidence=match.group(0)[:160],
                        score=0.14,
                    )
                )
        return matches

    def _score_instruction_density(self, text: str) -> list[InjectionFinding]:
        tokens = re.findall(r"\w+|[<>|{}()[\]`]+", text)
        if not tokens:
            return []

        instruction_markers = sum(
            1
            for token in tokens
            if token.lower() in {
                "ignore",
                "override",
                "system",
                "assistant",
                "user",
                "tool",
                "prompt",
                "instructions",
                "secret",
                "reveal",
                "only",
                "must",
                "never",
            }
        )
        density = instruction_markers / max(1, len(tokens))

        if density >= 0.12:
            return [
                InjectionFinding(
                    category="instruction_density",
                    severity=InjectionSeverity.HIGH,
                    evidence=f"density={density:.3f}",
                    score=min(0.18, density * 1.4),
                )
            ]
        if density >= 0.07:
            return [
                InjectionFinding(
                    category="instruction_density",
                    severity=InjectionSeverity.MEDIUM,
                    evidence=f"density={density:.3f}",
                    score=min(0.10, density),
                )
            ]
        return []

    def _aggregate_score(self, findings: Iterable[InjectionFinding]) -> float:
        score = 0.0
        for finding in findings:
            score += finding.score
        return min(1.0, score)

    def _max_severity(self, findings: Iterable[InjectionFinding]) -> InjectionSeverity:
        severity_rank = {
            InjectionSeverity.NONE: 0,
            InjectionSeverity.LOW: 1,
            InjectionSeverity.MEDIUM: 2,
            InjectionSeverity.HIGH: 3,
            InjectionSeverity.CRITICAL: 4,
        }
        result = InjectionSeverity.NONE
        for finding in findings:
            if severity_rank[finding.severity] > severity_rank[result]:
                result = finding.severity
        return result

    def _redaction_suggestions(self, findings: Iterable[InjectionFinding]) -> list[str]:
        suggestions = []
        seen = set()
        for finding in findings:
            if finding.category == "role_confusion" and "remove role overrides" not in seen:
                suggestions.append("remove role overrides or instruction override phrases")
                seen.add("remove role overrides")
            elif finding.category == "markup_abuse" and "strip markup" not in seen:
                suggestions.append("strip markup, fenced blocks, and control-token-like tags")
                seen.add("strip markup")
            elif finding.category == "escape_or_code_abuse" and "isolate escapes" not in seen:
                suggestions.append("isolate escape sequences and code-like payloads")
                seen.add("isolate escapes")
            elif finding.category == "nested_instruction" and "flatten structure" not in seen:
                suggestions.append("flatten nested instruction structures before passing to the model")
                seen.add("flatten structure")
        return suggestions


classifier = PromptInjectionClassifier()
