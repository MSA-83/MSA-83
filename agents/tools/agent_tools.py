"""Custom tools for Titanium agents."""

import os
import re
import subprocess
from urllib.parse import urlparse

import httpx

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


class FileListTool:
    """Tool for listing directory contents."""

    name = "file_lister"
    description = "List files and directories in a workspace path"

    def __init__(self, base_path: str = "/workspace"):
        self.base_path = base_path

    def run(self, dir_path: str = ".") -> str:
        full_path = os.path.join(self.base_path, dir_path)

        if not os.path.isdir(full_path):
            return f"Error: Directory not found: {full_path}"

        if not full_path.startswith(self.base_path):
            return "Error: Access denied - path outside workspace"

        try:
            entries = os.listdir(full_path)
            dirs = sorted([e for e in entries if os.path.isdir(os.path.join(full_path, e))])
            files = sorted([e for e in entries if os.path.isfile(os.path.join(full_path, e))])

            lines = [f"Directory: {dir_path}/", ""]
            if dirs:
                lines.append("Directories:")
                for d in dirs:
                    lines.append(f"  [DIR]  {d}/")
            if files:
                lines.append("Files:")
                for f in files:
                    fp = os.path.join(full_path, f)
                    size = os.path.getsize(fp)
                    size_str = f"{size:,}" if size > 1024 else f"{size} B"
                    lines.append(f"  [FILE] {f} ({size_str})")

            return "\n".join(lines)
        except Exception as e:
            return f"Error listing directory: {str(e)}"


class FileSearchTool:
    """Tool for searching files by pattern."""

    name = "file_searcher"
    description = "Search for files matching a glob pattern in the workspace"

    def __init__(self, base_path: str = "/workspace"):
        self.base_path = base_path

    def run(self, pattern: str, recursive: bool = True) -> str:
        import glob as glob_mod

        search_pattern = os.path.join(self.base_path, "**" if recursive else "", pattern)
        matches = glob_mod.glob(search_pattern, recursive=recursive)

        if not matches:
            return f"No files matching '{pattern}' found."

        rel_paths = sorted([os.path.relpath(m, self.base_path) for m in matches if m.startswith(self.base_path)])
        lines = [f"Found {len(rel_paths)} file(s) matching '{pattern}':", ""]
        for p in rel_paths:
            lines.append(f"  {p}")

        return "\n".join(lines)


class FileDeleteTool:
    """Tool for deleting files (with safety checks)."""

    name = "file_deleter"
    description = "Delete a file from the workspace"

    def __init__(self, base_path: str = "/workspace"):
        self.base_path = base_path

    def run(self, file_path: str) -> str:
        full_path = os.path.join(self.base_path, file_path)

        if not full_path.startswith(self.base_path):
            return "Error: Access denied - path outside workspace"

        if not os.path.exists(full_path):
            return f"Error: File not found: {full_path}"

        if os.path.isdir(full_path):
            return "Error: Cannot delete directories, only files."

        try:
            os.remove(full_path)
            return f"Successfully deleted: {file_path}"
        except Exception as e:
            return f"Error deleting file: {str(e)}"


class ShellTool:
    """Tool for executing shell commands (sandboxed)."""

    name = "shell_executor"
    description = "Execute a shell command in a sandboxed environment"

    ALLOWED_COMMANDS = [
        "ls",
        "cat",
        "grep",
        "find",
        "wc",
        "head",
        "tail",
        "pwd",
        "df",
        "du",
        "tree",
        "stat",
        "md5sum",
        "sha256sum",
    ]

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


class WebSearchTool:
    """Tool for searching the web for current information."""

    name = "web_search"
    description = "Search the web for current information, news, and technical documentation"

    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    def run(self, query: str) -> str:
        try:
            import urllib.parse
            import urllib.request

            encoded_query = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; TitaniumAgent/1.0)",
                },
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode("utf-8")

            results = self._parse_results(html)

            if not results:
                return f"No web search results found for: {query}"

            lines = [f"Web search results for '{query}':", ""]
            for i, r in enumerate(results[: self.max_results], 1):
                lines.append(f"[{i}] {r['title']}")
                lines.append(f"    URL: {r['url']}")
                if r.get("snippet"):
                    lines.append(f"    {r['snippet']}")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return f"Web search failed: {str(e)}"

    def _parse_results(self, html: str) -> list[dict]:
        results = []
        result_pattern = re.compile(
            r'<a[^>]*class="result[^"]*"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            re.DOTALL,
        )

        for match in result_pattern.finditer(html):
            url = match.group(1)
            title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
            snippet = re.sub(r"<[^>]+>", "", match.group(3)).strip()

            if url and title:
                results.append(
                    {
                        "title": title,
                        "url": url,
                        "snippet": snippet[:200],
                    }
                )

        if not results:
            links = re.findall(r'<a[^>]*href="([^"]*http[^"]*)"[^>]*>(.*?)</a>', html)
            for url, title in links[: self.max_results]:
                title = re.sub(r"<[^>]+>", "", title).strip()
                if title and len(title) > 10:
                    results.append(
                        {
                            "title": title,
                            "url": url,
                            "snippet": "",
                        }
                    )

        return results


class URLFetcherTool:
    """Tool for fetching and extracting content from URLs."""

    name = "url_fetcher"
    description = "Fetch and extract readable text content from a web page URL"

    MAX_CONTENT_LENGTH = 50000

    def run(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return f"Error: Only http/https URLs allowed. Got: {parsed.scheme}"

            blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "metadata.google.internal"}
            if parsed.hostname in blocked_hosts:
                return f"Error: Access to {parsed.hostname} is blocked for security reasons."

            if parsed.hostname:
                try:
                    import ipaddress

                    ip = ipaddress.ip_address(parsed.hostname)
                    if ip.is_private or ip.is_loopback or ip.is_link_local:
                        return "Error: Access to private/internal IPs is blocked."
                except ValueError:
                    pass

            response = httpx.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; TitaniumAgent/1.0)"},
                follow_redirects=True,
                timeout=15,
            )

            if response.status_code != 200:
                return f"Error: HTTP {response.status_code} for {url}"

            content = response.text
            if len(content) > self.MAX_CONTENT_LENGTH:
                content = content[: self.MAX_CONTENT_LENGTH] + "\n\n[Content truncated - exceeded length limit]"

            text = self._extract_text(content)

            return f"Content from {url}:\n\n{text}"

        except httpx.TimeoutException:
            return f"Error: Request timed out for {url}"
        except httpx.RequestError as e:
            return f"Error fetching URL: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"

    def _extract_text(self, html: str) -> str:
        text = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", html)
        text = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"&\w+;", " ", text)
        text = re.sub(r"&#\d+;", " ", text)
        text = text.strip()

        paragraphs = re.split(r"\n{2,}", text)
        return "\n\n".join(p.strip() for p in paragraphs if p.strip())[: self.MAX_CONTENT_LENGTH]


class CodeExecutorTool:
    """Tool for executing code snippets safely with sandboxing."""

    name = "code_executor"
    description = "Execute Python code in a sandboxed environment"

    BLOCKED_MODULES = {
        "os",
        "sys",
        "subprocess",
        "multiprocessing",
        "threading",
        "socket",
        "urllib",
        "http",
        "requests",
        "ftplib",
        "smtplib",
        "shutil",
        "pathlib",
        "importlib",
        "ctypes",
        "pickle",
        "marshal",
        "inspect",
        "traceback",
        "pdb",
    }

    BLOCKED_BUILTINS = {"eval", "exec", "compile", "open", "input", "exit", "quit"}

    def run(self, code: str, timeout: int = 10) -> str:
        for module in self.BLOCKED_MODULES:
            if f"import {module}" in code or f"from {module}" in code:
                return f"Error: Import of '{module}' is blocked for security reasons."

        for builtin in self.BLOCKED_BUILTINS:
            if re.search(rf"\b{builtin}\s*\(", code):
                return f"Error: Use of '{builtin}()' is blocked for security reasons."

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


class CVESearchTool:
    """Tool for looking up CVE vulnerability information."""

    name = "cve_search"
    description = "Look up CVE vulnerability details by CVE ID or search by keyword"

    def run(self, query: str) -> str:
        try:
            query = query.strip()

            if re.match(r"CVE-\d{4}-\d+", query, re.IGNORECASE):
                return self._lookup_cve(query.upper())

            return self._search_cves(query)

        except Exception as e:
            return f"CVE search failed: {str(e)}"

    def _lookup_cve(self, cve_id: str) -> str:
        try:
            url = f"https://cveawg.mitre.org/api/cve/{cve_id}"
            response = httpx.get(url, timeout=10)

            if response.status_code != 200:
                return f"No information found for {cve_id}"

            data = response.json()
            cve_info = data.get("cveMetadata", {})
            containers = data.get("containers", {})
            cna = containers.get("cna", {})

            descriptions = cna.get("descriptions", [])
            desc = descriptions[0].get("value", "No description available") if descriptions else "No description"

            affected = cna.get("affected", [])
            affected_str = "Unknown"
            if affected:
                products = [a.get("product", "unknown") for a in affected[:5]]
                affected_str = ", ".join(products)

            references = cna.get("references", [])
            ref_urls = [r.get("url", "") for r in references[:3] if r.get("url")]

            severity = "Unknown"
            metrics = cna.get("metrics", [])
            if metrics:
                for m in metrics:
                    if "cvssV3_1" in m or "cvssV3_0" in m:
                        cvss = m.get("cvssV3_1", m.get("cvssV3_0", {}))
                        score = cvss.get("baseScore", "N/A")
                        severity = cvss.get("baseSeverity", f"Score: {score}")
                        break

            lines = [
                f"CVE: {cve_id}",
                f"Severity: {severity}",
                f"State: {cve_info.get('state', 'Unknown')}",
                f"Date Published: {cve_info.get('datePublished', 'Unknown')}",
                "",
                f"Description:\n{desc[:500]}",
                "",
                f"Affected Products: {affected_str}",
            ]

            if ref_urls:
                lines.append("\nReferences:")
                for r in ref_urls:
                    lines.append(f"  - {r}")

            return "\n".join(lines)

        except httpx.RequestError:
            return f"Error: Could not connect to CVE database for {cve_id}"
        except Exception as e:
            return f"Error looking up CVE: {str(e)}"

    def _search_cves(self, keyword: str) -> str:
        try:
            url = f"https://cveawg.mitre.org/api/cve?keywordSearch={keyword}&countOnly=false"
            response = httpx.get(url, timeout=10)

            if response.status_code != 200:
                return f"Search failed for keyword: {keyword}"

            data = response.json()
            total = data.get("totalResults", 0)
            cves = data.get("vulnerabilities", [])[:10]

            if not cves:
                return f"No CVEs found matching '{keyword}'."

            lines = [f"Found {total} CVE(s) matching '{keyword}' (showing first {len(cves)}):", ""]
            for entry in cves:
                cve_id = entry.get("cveMetadata", {}).get("cveId", "Unknown")
                containers = entry.get("containers", {})
                cna = containers.get("cna", {})
                desc = cna.get("descriptions", [{}])[0].get("value", "")[:150]
                lines.append(f"- {cve_id}: {desc}")

            return "\n".join(lines)

        except httpx.RequestError:
            return "Error: Could not connect to CVE database."
        except Exception as e:
            return f"Error searching CVEs: {str(e)}"


class CodeAnalysisTool:
    """Tool for static code analysis (AST-based)."""

    name = "code_analyzer"
    description = "Analyze Python code for potential issues using AST parsing"

    def run(self, code: str) -> str:
        try:
            import ast

            tree = ast.parse(code)
            issues = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = ""
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr

                    if func_name in ("eval", "exec"):
                        issues.append(f"DANGEROUS: Use of {func_name}() at line {node.lineno}")
                    if func_name in ("os.system", "popen"):
                        issues.append(f"WARNING: Potential command injection at line {node.lineno}")

                if isinstance(node, ast.ExceptHandler) and not node.name:
                    issues.append(f"WARNING: Bare except clause at line {node.lineno}")

            if not issues:
                return "No issues detected in the code."

            lines = [f"Found {len(issues)} potential issue(s):", ""]
            for issue in issues:
                lines.append(f"- {issue}")

            return "\n".join(lines)

        except SyntaxError as e:
            return f"Syntax error in code: {e}"
        except Exception as e:
            return f"Analysis failed: {str(e)}"


def get_agent_tools(agent_type: str) -> list:
    """Get the appropriate tools for an agent type."""
    tool_sets = {
        "researcher": [WebSearchTool(), URLFetcherTool(), RAGSearchTool(), FileReadTool(), FileListTool(), ShellTool()],
        "coder": [
            FileReadTool(),
            FileWriteTool(),
            FileListTool(),
            FileSearchTool(),
            CodeExecutorTool(),
            CodeAnalysisTool(),
            ShellTool(),
        ],
        "analyst": [RAGSearchTool(), WebSearchTool(), URLFetcherTool(), CodeExecutorTool(), FileReadTool()],
        "security": [
            CVESearchTool(),
            WebSearchTool(),
            URLFetcherTool(),
            RAGSearchTool(),
            FileReadTool(),
            FileSearchTool(),
            CodeAnalysisTool(),
            ShellTool(),
        ],
        "writer": [WebSearchTool(), URLFetcherTool(), RAGSearchTool(), FileReadTool(), FileWriteTool()],
    }

    return tool_sets.get(agent_type, [RAGSearchTool()])
