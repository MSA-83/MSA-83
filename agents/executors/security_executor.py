"""Security audit executor agent."""


from agents.executors.base import BaseExecutor, ExecutorStatus, TaskResult
from backend.security.prompt_injection import detector as injection_detector
from backend.services.ollama_service import ollama_service

VULNERABILITY_CATEGORIES = [
    "SQL Injection",
    "Cross-Site Scripting (XSS)",
    "Authentication Bypass",
    "Authorization Issues",
    "Data Exposure",
    "Rate Limiting",
    "Input Validation",
    "Session Management",
    "CORS Misconfiguration",
    "Prompt Injection",
]


class SecurityAuditExecutor(BaseExecutor):
    """Execute security audit tasks."""

    def __init__(self):
        super().__init__(
            name="security_audit_executor",
            description="Analyze code and configurations for security vulnerabilities",
        )

    def validate_input(self, task_input: str) -> bool:
        return bool(task_input.strip()) and len(task_input) <= 10000

    async def execute(
        self,
        task_input: str,
        context: dict | None = None,
    ) -> TaskResult:
        injection_result = injection_detector.analyze(task_input)

        system_prompt = (
            "You are a cybersecurity specialist. "
            "Analyze the provided code/configuration for security vulnerabilities. "
            "For each finding, provide: severity (Critical/High/Medium/Low), "
            "description, affected area, and remediation steps. "
            "Be thorough but practical."
        )

        response = await ollama_service.chat(
            model="llama3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task_input},
            ],
        )

        output = response.get("message", {}).get("content", "")

        findings = self._parse_findings(output)

        return TaskResult(
            status=ExecutorStatus.COMPLETED,
            output=output,
            metadata={
                "findings_count": len(findings),
                "categories_found": [f["category"] for f in findings],
                "injection_detected": injection_result["is_suspicious"],
                "token_count": len(output.split()),
            },
        )

    def _parse_findings(self, output: str) -> list[dict]:
        findings = []
        for category in VULNERABILITY_CATEGORIES:
            if category.lower() in output.lower():
                findings.append({"category": category, "severity": "Unknown"})
        return findings


security_audit_executor = SecurityAuditExecutor()
