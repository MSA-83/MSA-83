"""Custom tools for Titanium agents."""

import ast
import base64
import csv
import difflib
import hashlib
import io
import json
import math
import os
import re
import subprocess
import textwrap
import xml.etree.ElementTree as ET
from datetime import datetime
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


class CalculatorTool:
    """Tool for evaluating mathematical expressions safely."""

    name = "calculator"
    description = "Evaluate mathematical expressions including trig, log, sqrt, and constants"

    ALLOWED_NAMES = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "ceil": math.ceil,
        "floor": math.floor,
        "factorial": math.factorial,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
        "inf": math.inf,
    }

    BLOCKED_PATTERNS = [
        r"\bimport\b",
        r"\bopen\b",
        r"\bexec\b",
        r"\beval\b",
        r"\b__\w+__\b",
        r"\bsystem\b",
        r"\bsubprocess\b",
        r"\bos\.",
    ]

    def run(self, expression: str) -> str:
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, expression):
                return f"Error: Expression contains blocked pattern."

        if re.search(r"[^0-9+\-*/().%\s\w,]", expression):
            pass

        try:
            result = eval(expression, {"__builtins__": {}}, self.ALLOWED_NAMES)
            if isinstance(result, float) and result != result:
                return "Result: NaN"
            if result == math.inf or result == -math.inf:
                return "Result: Infinity"
            return f"Result: {result}"
        except Exception as e:
            return f"Error evaluating expression: {str(e)}"


class RegexTesterTool:
    """Tool for testing regular expressions against text."""

    name = "regex_tester"
    description = "Test a regex pattern against text and see all matches, groups, and positions"

    def run(self, pattern: str, text: str, flags: str = "") -> str:
        try:
            flag_value = 0
            for f in flags.split(","):
                f = f.strip().lower()
                if f == "ignorecase":
                    flag_value |= re.IGNORECASE
                elif f == "multiline":
                    flag_value |= re.MULTILINE
                elif f == "dotall":
                    flag_value |= re.DOTALL

            compiled = re.compile(pattern, flag_value)

            matches = list(compiled.finditer(text))
            if not matches:
                return f"No matches found for pattern: {pattern}"

            lines = [f"Found {len(matches)} match(es) for pattern '{pattern}':", ""]
            for i, m in enumerate(matches, 1):
                lines.append(f"Match {i}: '{m.group()}' at position {m.start()}-{m.end()}")
                if m.groups():
                    for gi, g in enumerate(m.groups(), 1):
                        lines.append(f"  Group {gi}: '{g}'")
                if m.groupdict():
                    for k, v in m.groupdict().items():
                        lines.append(f"  {k}: '{v}'")
                lines.append("")

            subs = compiled.sub("MATCH", text, count=0)
            lines.append(f"Substitution preview (matches → MATCH):")
            preview = subs[:300]
            if len(subs) > 300:
                preview += "..."
            lines.append(preview)

            return "\n".join(lines)
        except re.error as e:
            return f"Invalid regex pattern: {str(e)}"
        except Exception as e:
            return f"Regex test failed: {str(e)}"


class JSONFormatterTool:
    """Tool for validating, formatting, and transforming JSON."""

    name = "json_formatter"
    description = "Validate, prettify, minify, or extract paths from JSON data"

    def run(self, json_str: str, action: str = "prettify", path: str = "") -> str:
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return f"Invalid JSON: {str(e)}"

        try:
            if action == "prettify":
                return json.dumps(data, indent=2, ensure_ascii=False)
            elif action == "minify":
                return json.dumps(data, separators=(",", ":"), ensure_ascii=False)
            elif action == "keys":
                keys = self._extract_keys(data)
                return f"Keys found:\n" + "\n".join(f"  - {k}" for k in keys)
            elif action == "extract" and path:
                value = self._extract_path(data, path)
                return json.dumps(value, indent=2, ensure_ascii=False)
            elif action == "stats":
                return self._json_stats(data)
            else:
                return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"JSON operation failed: {str(e)}"

    def _extract_keys(self, data, prefix="") -> list[str]:
        keys = []
        if isinstance(data, dict):
            for k, v in data.items():
                full_key = f"{prefix}.{k}" if prefix else k
                keys.append(full_key)
                keys.extend(self._extract_keys(v, full_key))
        elif isinstance(data, list) and data:
            keys.extend(self._extract_keys(data[0], f"{prefix}[0]"))
        return keys

    def _extract_path(self, data, path: str):
        parts = re.split(r"\.|\[|\]", path)
        parts = [p for p in parts if p]
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current[part]
            elif isinstance(current, list):
                current = current[int(part)]
            else:
                raise KeyError(f"Cannot navigate into {type(current).__name__}")
        return current

    def _json_stats(self, data) -> str:
        def count(obj):
            if isinstance(obj, dict):
                return sum(count(v) for v in obj.values()) + len(obj)
            elif isinstance(obj, list):
                return sum(count(i) for i in obj) + 1
            return 1

        total = count(data)
        return f"Total elements: {total}\nType: {type(data).__name__}\nSize: {len(json.dumps(data))} bytes"


class DiffGeneratorTool:
    """Tool for generating diffs between two text/code blocks."""

    name = "diff_generator"
    description = "Generate a unified diff between two text or code blocks"

    def run(self, original: str, modified: str, from_file: str = "a", to_file: str = "b") -> str:
        try:
            orig_lines = original.splitlines(keepends=True)
            mod_lines = modified.splitlines(keepends=True)

            diff = difflib.unified_diff(
                orig_lines,
                mod_lines,
                fromfile=from_file,
                tofile=to_file,
            )

            result = "".join(diff)
            if not result:
                return "No differences found."
            return result
        except Exception as e:
            return f"Diff generation failed: {str(e)}"


class ImageMetadataTool:
    """Tool for extracting metadata from image files."""

    name = "image_metadata"
    description = "Extract metadata (dimensions, format, size, EXIF) from an image file"

    def run(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return f"Error: File not found: {file_path}"

        try:
            size = os.path.getsize(file_path)
            size_str = self._format_size(size)

            ext = os.path.splitext(file_path)[1].lower()
            format_map = {
                ".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG",
                ".gif": "GIF", ".bmp": "BMP", ".webp": "WEBP",
                ".tiff": "TIFF", ".tif": "TIFF", ".svg": "SVG",
                ".ico": "ICO", ".avif": "AVIF",
            }
            fmt = format_map.get(ext, ext.upper().lstrip("."))

            lines = [
                f"File: {os.path.basename(file_path)}",
                f"Format: {fmt}",
                f"Size: {size_str}",
            ]

            try:
                with open(file_path, "rb") as f:
                    header = f.read(32)

                if header[:2] == b"\xff\xd8":
                    lines.append("Signature: JPEG")
                    width, height = self._parse_jpeg_size(file_path)
                    if width and height:
                        lines.append(f"Dimensions: {width}x{height}")
                elif header[:8] == b"\x89PNG\r\n\x1a\n":
                    lines.append("Signature: PNG")
                    w = int.from_bytes(header[16:20], "big")
                    h = int.from_bytes(header[20:24], "big")
                    lines.append(f"Dimensions: {w}x{h}")
                elif header[:6] == b"GIF87a" or header[:6] == b"GIF89a":
                    lines.append("Signature: GIF")
                    w = int.from_bytes(header[6:8], "little")
                    h = int.from_bytes(header[8:10], "little")
                    lines.append(f"Dimensions: {w}x{h}")
                elif header[:4] == b"RIFF" and header[8:12] == b"WEBP":
                    lines.append("Signature: WEBP")
            except Exception:
                pass

            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            lines.append(f"SHA-256: {sha256.hexdigest()[:16]}...")

            return "\n".join(lines)
        except Exception as e:
            return f"Failed to read image metadata: {str(e)}"

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _parse_jpeg_size(self, path: str) -> tuple:
        try:
            with open(path, "rb") as f:
                data = f.read()
            pos = 2
            while pos < len(data):
                if data[pos] != 0xFF:
                    pos += 1
                    continue
                marker = data[pos + 1]
                if marker == 0xC0 or marker == 0xC2:
                    h = int.from_bytes(data[pos + 5 : pos + 7], "big")
                    w = int.from_bytes(data[pos + 7 : pos + 9], "big")
                    return (w, h)
                segment_len = int.from_bytes(data[pos + 2 : pos + 4], "big")
                pos += 2 + segment_len
        except Exception:
            pass
        return (None, None)


class CSVTool:
    """Tool for parsing and transforming CSV data."""

    name = "csv_tool"
    description = "Parse, validate, count, or convert CSV data to JSON and vice versa"

    def run(self, data: str, action: str = "parse", delimiter: str = ",") -> str:
        try:
            if action == "parse":
                reader = csv.DictReader(io.StringIO(data), delimiter=delimiter)
                rows = list(reader)
                if not rows:
                    return "No data rows found."
                lines = [f"CSV parsed: {len(rows)} rows, {len(rows[0].keys())} columns"]
                lines.append(f"Columns: {', '.join(rows[0].keys())}")
                lines.append("")
                for i, row in enumerate(rows[:5], 1):
                    lines.append(f"Row {i}:")
                    for k, v in row.items():
                        lines.append(f"  {k}: {v}")
                if len(rows) > 5:
                    lines.append(f"... and {len(rows) - 5} more rows")
                return "\n".join(lines)

            elif action == "to_json":
                reader = csv.DictReader(io.StringIO(data), delimiter=delimiter)
                rows = list(reader)
                return json.dumps(rows, indent=2, ensure_ascii=False)

            elif action == "from_json":
                json_data = json.loads(data)
                if not isinstance(json_data, list) or not json_data:
                    return "Error: JSON must be a non-empty array of objects."
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=json_data[0].keys())
                writer.writeheader()
                writer.writerows(json_data)
                return output.getvalue()

            elif action == "validate":
                reader = csv.reader(io.StringIO(data), delimiter=delimiter)
                rows = list(reader)
                if not rows:
                    return "Error: Empty CSV."
                header_len = len(rows[0])
                invalid = []
                for i, row in enumerate(rows[1:], 2):
                    if len(row) != header_len:
                        invalid.append(i)
                if invalid:
                    return f"CSV validation: {len(invalid)} row(s) have wrong column count: rows {invalid}"
                return f"CSV valid: {len(rows) - 1} rows, {header_len} columns"

            else:
                return f"Unknown action: {action}. Supported: parse, to_json, from_json, validate"
        except json.JSONDecodeError as e:
            return f"JSON parse error: {str(e)}"
        except Exception as e:
            return f"CSV operation failed: {str(e)}"


class XMLTool:
    """Tool for parsing and querying XML data."""

    name = "xml_tool"
    description = "Parse, validate, and extract data from XML documents"

    def run(self, xml_str: str, action: str = "parse", xpath: str = "") -> str:
        try:
            root = ET.fromstring(xml_str)

            if action == "parse":
                return self._tree_summary(root)
            elif action == "find" and xpath:
                elements = root.findall(xpath)
                if not elements:
                    return f"No elements found for path: {xpath}"
                lines = [f"Found {len(elements)} element(s) for '{xpath}':", ""]
                for elem in elements[:20]:
                    text = (elem.text or "").strip()
                    attrs = dict(elem.attrib)
                    line = f"<{elem.tag}"
                    if attrs:
                        line += " " + " ".join(f'{k}="{v}"' for k, v in attrs.items())
                    line += f">{text}" if text else f"/>"
                    lines.append(line)
                if len(elements) > 20:
                    lines.append(f"... and {len(elements) - 20} more")
                return "\n".join(lines)
            elif action == "validate":
                return f"Valid XML. Root element: <{root.tag}>"
            elif action == "stats":
                count = sum(1 for _ in root.iter())
                tags = set(elem.tag for elem in root.iter())
                return f"Total elements: {count}\nUnique tags: {len(tags)}\nTags: {', '.join(sorted(tags))}"
            else:
                return self._tree_summary(root)
        except ET.ParseError as e:
            return f"XML parse error: {str(e)}"
        except Exception as e:
            return f"XML operation failed: {str(e)}"

    def _tree_summary(self, root: ET.Element, indent: int = 0) -> str:
        lines = []
        prefix = "  " * indent
        text = (root.text or "").strip()[:80]
        attr_str = ""
        if root.attrib:
            attr_str = " " + " ".join(f'{k}="{v}"' for k, v in root.attrib.items())
        line = f"{prefix}<{root.tag}{attr_str}>"
        if text:
            line += f" {text}"
        lines.append(line)
        children = list(root)
        if children:
            for child in children[:10]:
                lines.extend(self._tree_summary(child, indent + 1).split("\n"))
            if len(children) > 10:
                lines.append(f"{prefix}  ... and {len(children) - 10} more children")
        return "\n".join(lines)


class APITesterTool:
    """Tool for making HTTP requests to test APIs."""

    name = "api_tester"
    description = "Make HTTP requests (GET/POST/PUT/DELETE/PATCH) with headers and body to test APIs"

    BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "metadata.google.internal"}

    def run(self, url: str, method: str = "GET", headers: str = "", body: str = "") -> str:
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return f"Error: Only http/https URLs allowed."
            if parsed.hostname in self.BLOCKED_HOSTS:
                return f"Error: Access to {parsed.hostname} is blocked."
            try:
                import ipaddress
                ip = ipaddress.ip_address(parsed.hostname)
                if ip.is_private or ip.is_loopback:
                    return "Error: Private IPs blocked."
            except ValueError:
                pass

            req_headers = {}
            if headers:
                for line in headers.split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        req_headers[k.strip()] = v.strip()

            method = method.upper()
            if method not in ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"):
                return f"Error: Unsupported method: {method}"

            start = datetime.utcnow()
            response = httpx.request(
                method, url,
                headers=req_headers,
                content=body if body else None,
                follow_redirects=True,
                timeout=15,
            )
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000

            lines = [
                f"HTTP {response.status_code} {response.reason_phrase}",
                f"Time: {elapsed:.0f}ms",
                f"Content-Type: {response.headers.get('content-type', 'unknown')}",
                f"Size: {len(response.content):,} bytes",
                "",
                "Response:",
            ]

            if response.text:
                preview = response.text[:5000]
                try:
                    formatted = json.dumps(json.loads(preview), indent=2)
                    lines.append(formatted)
                except (json.JSONDecodeError, ValueError):
                    lines.append(preview)

            return "\n".join(lines)
        except httpx.TimeoutException:
            return "Error: Request timed out."
        except Exception as e:
            return f"Request failed: {str(e)}"


class HashTool:
    """Tool for computing cryptographic hashes of strings or files."""

    name = "hash_tool"
    description = "Compute MD5, SHA-1, SHA-256, or SHA-512 hashes of text or file contents"

    def run(self, input_str: str, algorithm: str = "sha256", is_file: bool = False) -> str:
        algos = {
            "md5": hashlib.md5,
            "sha1": hashlib.sha1,
            "sha256": hashlib.sha256,
            "sha512": hashlib.sha512,
        }

        if algorithm.lower() not in algos:
            return f"Error: Unsupported algorithm. Supported: {', '.join(algos.keys())}"

        try:
            h = algos[algorithm.lower()]()
            if is_file:
                if not os.path.exists(input_str):
                    return f"Error: File not found: {input_str}"
                with open(input_str, "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        h.update(chunk)
                return f"{algorithm.upper()}({os.path.basename(input_str)}): {h.hexdigest()}"
            else:
                h.update(input_str.encode("utf-8"))
                return f"{algorithm.upper()}: {h.hexdigest()}"
        except Exception as e:
            return f"Hash computation failed: {str(e)}"


class Base64Tool:
    """Tool for encoding and decoding Base64 data."""

    name = "base64_tool"
    description = "Encode text to Base64 or decode Base64 strings"

    def run(self, data: str, action: str = "encode") -> str:
        try:
            if action == "encode":
                encoded = base64.b64encode(data.encode("utf-8")).decode("utf-8")
                return f"Base64 encoded:\n{encoded}"
            elif action == "decode":
                decoded = base64.b64decode(data).decode("utf-8")
                return f"Base64 decoded:\n{decoded}"
            else:
                return f"Unknown action: {action}. Supported: encode, decode"
        except Exception as e:
            return f"Base64 operation failed: {str(e)}"


class DateTool:
    """Tool for date/time calculations and formatting."""

    name = "date_tool"
    description = "Get current time, parse dates, calculate differences, and format timestamps"

    def run(self, action: str = "now", date1: str = "", date2: str = "", format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        try:
            if action == "now":
                now = datetime.utcnow()
                return f"Current UTC: {now.strftime(format_str)}\nISO 8601: {now.isoformat()}\nTimestamp: {now.timestamp():.0f}"
            elif action == "parse" and date1:
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"]:
                    try:
                        dt = datetime.strptime(date1, fmt)
                        return f"Parsed: {dt}\nDay: {dt.strftime('%A')}\nWeek: {dt.isocalendar()[1]}\nDay of year: {dt.timetuple().tm_yday}"
                    except ValueError:
                        continue
                return f"Could not parse date: {date1}"
            elif action == "diff" and date1 and date2:
                d1 = self._parse_date(date1)
                d2 = self._parse_date(date2)
                if d1 and d2:
                    delta = abs(d2 - d1)
                    return f"Difference: {delta.days} days, {delta.seconds // 3600} hours, {(delta.seconds % 3600) // 60} minutes"
                return "Could not parse one or both dates."
            elif action == "format" and date1:
                dt = self._parse_date(date1)
                if dt:
                    return f"Formatted ({format_str}): {dt.strftime(format_str)}"
                return f"Could not parse date: {date1}"
            else:
                return f"Usage: action=now|parse|diff|format"
        except Exception as e:
            return f"Date operation failed: {str(e)}"

    def _parse_date(self, s: str) -> datetime | None:
        for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"]:
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None


class MarkdownTool:
    """Tool for converting between Markdown and HTML."""

    name = "markdown_tool"
    description = "Convert Markdown to HTML or extract headings/links from Markdown text"

    def run(self, markdown_str: str, action: str = "to_html") -> str:
        try:
            if action == "to_html":
                html = self._md_to_html(markdown_str)
                return html
            elif action == "headings":
                headings = re.findall(r'^(#{1,6})\s+(.+)$', markdown_str, re.MULTILINE)
                if not headings:
                    return "No headings found."
                lines = ["Headings:"]
                for hashes, text in headings:
                    level = len(hashes)
                    lines.append(f"  {'  ' * (level - 1)}H{level}: {text}")
                return "\n".join(lines)
            elif action == "links":
                links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', markdown_str)
                if not links:
                    return "No links found."
                lines = ["Links:"]
                for text, url in links:
                    lines.append(f"  {text} -> {url}")
                return "\n".join(lines)
            elif action == "stats":
                words = len(markdown_str.split())
                lines_count = len(markdown_str.splitlines())
                headings = len(re.findall(r'^#{1,6}\s+', markdown_str, re.MULTILINE))
                links = len(re.findall(r'\[.+?\]\(.+?\)', markdown_str))
                code_blocks = len(re.findall(r'```', markdown_str)) // 2
                return f"Words: {words}\nLines: {lines_count}\nHeadings: {headings}\nLinks: {links}\nCode blocks: {code_blocks}\nChars: {len(markdown_str)}"
            else:
                return f"Unknown action: {action}. Supported: to_html, headings, links, stats"
        except Exception as e:
            return f"Markdown operation failed: {str(e)}"

    def _md_to_html(self, md: str) -> str:
        lines = md.split("\n")
        html = []
        in_code = False
        in_ul = False
        for line in lines:
            if line.startswith("```"):
                if in_code:
                    html.append("</code></pre>")
                    in_code = False
                else:
                    if in_ul:
                        html.append("</ul>")
                        in_ul = False
                    html.append("<pre><code>")
                    in_code = True
                continue
            if in_code:
                html.append(line)
                continue
            if in_ul and not line.startswith("- "):
                html.append("</ul>")
                in_ul = False
            m = re.match(r'^(#{1,6})\s+(.+)$', line)
            if m:
                level = len(m.group(1))
                html.append(f"<h{level}>{m.group(2)}</h{level}>")
            elif line.startswith("- "):
                if not in_ul:
                    html.append("<ul>")
                    in_ul = True
                html.append(f"  <li>{line[2:]}</li>")
            elif line.startswith("> "):
                html.append(f"<blockquote>{line[2:]}</blockquote>")
            elif line.strip() == "":
                pass
            else:
                text = line
                text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
                text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
                text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
                text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
                html.append(f"<p>{text}</p>")
        if in_ul:
            html.append("</ul>")
        return "\n".join(html)


def get_agent_tools(agent_type: str) -> list:
    """Get the appropriate tools for an agent type."""
    tool_sets = {
        "researcher": [
            WebSearchTool(), URLFetcherTool(), RAGSearchTool(), FileReadTool(), FileListTool(),
            ShellTool(), MarkdownTool(), DateTool(), APITesterTool(),
        ],
        "coder": [
            FileReadTool(), FileWriteTool(), FileListTool(), FileSearchTool(), FileDeleteTool(),
            CodeExecutorTool(), CodeAnalysisTool(), ShellTool(), DiffGeneratorTool(),
            RegexTesterTool(), HashTool(), Base64Tool(),
        ],
        "analyst": [
            RAGSearchTool(), WebSearchTool(), URLFetcherTool(), CodeExecutorTool(), FileReadTool(),
            JSONFormatterTool(), CSVTool(), XMLTool(), CalculatorTool(), MarkdownTool(),
        ],
        "security": [
            CVESearchTool(), WebSearchTool(), URLFetcherTool(), RAGSearchTool(), FileReadTool(),
            FileSearchTool(), CodeAnalysisTool(), ShellTool(), HashTool(), APITesterTool(),
        ],
        "writer": [
            WebSearchTool(), URLFetcherTool(), RAGSearchTool(), FileReadTool(), FileWriteTool(),
            MarkdownTool(), JSONFormatterTool(), Base64Tool(), DateTool(),
        ],
        "general": [
            CalculatorTool(), DateTool(), HashTool(), Base64Tool(), JSONFormatterTool(),
            MarkdownTool(), WebSearchTool(), RAGSearchTool(),
        ],
    }

    return tool_sets.get(agent_type, [RAGSearchTool()])
