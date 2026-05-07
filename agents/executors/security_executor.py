"""Security audit executor agent."""

import re

from agents.executors.base import BaseExecutor, ExecutorStatus, TaskResult
from agents.tools.agent_tools import CodeAnalysisTool, CVESearchTool
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
        self.cve_search = CVESearchTool()
        self.code_analyzer = CodeAnalysisTool()

    def validate_input(self, task_input: str) -> bool:
        return bool(task_input.strip()) and len(task_input) <= 10000

    async def execute(
        self,
        task_input: str,
        context: dict | None = None,
    ) -> TaskResult:
        injection_result = injection_detector.analyze(task_input)

        static_analysis = ""
        if context and context.get("language", "").lower() == "python":
            static_analysis = self.code_analyzer.run(task_input)
            if static_analysis.startswith("No issues") or static_analysis.startswith("Syntax error"):
                static_analysis = ""

        cve_context = ""
        cve_ids_found = []
        cve_matches = re.findall(r"CVE-\d{4}-\d+", task_input, re.IGNORECASE)
        for cve_id in cve_matches[:5]:
            cve_info = self.cve_search._lookup_cve(cve_id.upper())
            if cve_info:
                cve_ids_found.append(cve_id.upper())
                cve_context += f"\n{cve_info}\n"

        if context and context.get("dependencies"):
            deps = context["dependencies"] if isinstance(context["dependencies"], list) else []
            for dep in deps[:3]:
                dep_name = dep.split("==")[0].split(">=")[0].split("<")[0].strip()
                if dep_name:
                    search_result = self.cve_search._search_cves(dep_name)
                    if "No CVEs found" not in search_result:
                        cve_context += f"\nCVEs for {dep_name}:\n{search_result}\n"

        system_prompt = (
            "You are a cybersecurity specialist. "
            "Analyze the provided code/configuration for security vulnerabilities. "
            "For each finding, provide: severity (Critical/High/Medium/Low), "
            "description, affected area, and remediation steps. "
            "Be thorough but practical."
        )

        user_content = task_input
        context_parts = []
        if static_analysis:
            context_parts.append(f"Static analysis findings:\n{static_analysis}")
        if cve_context:
            context_parts.append(f"Known vulnerability data:\n{cve_context[:2000]}")

        if context_parts:
            user_content = "\n\n".join(context_parts) + f"\n\n---\n\nCode/Config to audit:\n{task_input}"

        response = await ollama_service.chat(
            model="llama3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
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
                "static_analysis_issues": len([l for l in static_analysis.split("\n") if l.startswith("-")]) if static_analysis else 0,
                "cves_found": cve_ids_found,
                "token_count": len(output.split()),
            },
        )

    def _parse_findings(self, output: str) -> list[dict]:
        findings = []
        for category in VULNERABILITY_CATEGORIES:
            if category.lower() in output.lower():
                severity = self._extract_severity(output, category)
                findings.append({"category": category, "severity": severity})
        return findings

    def _extract_severity(self, output: str, category: str) -> str:
        patterns = [
            rf"{category}.*?(Critical|High|Medium|Low)",
            rf"(Critical|High|Medium|Low).*?{category}",
            rf"severity.*?(Critical|High|Medium|Low)",
        ]
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1).capitalize()
        return "Unknown"


security_audit_executor = SecurityAuditExecutor()
