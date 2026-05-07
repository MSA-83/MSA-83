"""Tests for new agent tools."""

import json

from agents.tools.agent_tools import (
    APITesterTool,
    Base64Tool,
    CSVTool,
    CalculatorTool,
    DateTool,
    DiffGeneratorTool,
    HashTool,
    ImageMetadataTool,
    JSONFormatterTool,
    MarkdownTool,
    RegexTesterTool,
    XMLTool,
    get_agent_tools,
)


class TestCalculatorTool:
    def test_basic_math(self):
        tool = CalculatorTool()
        result = tool.run("2 + 3 * 4")
        assert "Result: 14" in result

    def test_math_functions(self):
        tool = CalculatorTool()
        result = tool.run("sqrt(16)")
        assert "Result: 4.0" in result

    def test_trigonometry(self):
        tool = CalculatorTool()
        result = tool.run("sin(0)")
        assert "Result: 0.0" in result

    def test_constants(self):
        tool = CalculatorTool()
        result = tool.run("pi")
        assert "3.14" in result

    def test_blocked_import(self):
        tool = CalculatorTool()
        result = tool.run("__import__('os')")
        assert "blocked" in result.lower()

    def test_factorial(self):
        tool = CalculatorTool()
        result = tool.run("factorial(5)")
        assert "Result: 120" in result

    def test_log(self):
        tool = CalculatorTool()
        result = tool.run("log(10)")
        assert "2.30" in result


class TestRegexTesterTool:
    def test_basic_match(self):
        tool = RegexTesterTool()
        result = tool.run(r"\d+", "abc 123 def 456")
        assert "2 match" in result

    def test_groups(self):
        tool = RegexTesterTool()
        result = tool.run(r"(\w+)=(\d+)", "foo=42 bar=99")
        assert "Group" in result

    def test_no_match(self):
        tool = RegexTesterTool()
        result = tool.run(r"xyz", "hello world")
        assert "No matches" in result

    def test_invalid_pattern(self):
        tool = RegexTesterTool()
        result = tool.run(r"[invalid", "test")
        assert "Invalid regex" in result

    def test_substitution_preview(self):
        tool = RegexTesterTool()
        result = tool.run(r"\d+", "abc 123 def")
        assert "Substitution preview" in result


class TestJSONFormatterTool:
    def test_prettify(self):
        tool = JSONFormatterTool()
        result = tool.run('{"a":1,"b":2}')
        assert '"a": 1' in result

    def test_minify(self):
        tool = JSONFormatterTool()
        result = tool.run('{\n  "a": 1\n}', action="minify")
        assert "\n" not in result

    def test_extract_keys(self):
        tool = JSONFormatterTool()
        result = tool.run('{"name":"test","nested":{"x":1}}', action="keys")
        assert "name" in result
        assert "nested.x" in result

    def test_extract_path(self):
        tool = JSONFormatterTool()
        result = tool.run('{"users":[{"name":"alice"}]}', action="extract", path="users[0].name")
        assert "alice" in result

    def test_stats(self):
        tool = JSONFormatterTool()
        result = tool.run('{"a":1,"b":[1,2,3]}', action="stats")
        assert "elements" in result.lower()

    def test_invalid_json(self):
        tool = JSONFormatterTool()
        result = tool.run("{invalid}")
        assert "Invalid JSON" in result


class TestDiffGeneratorTool:
    def test_no_diff(self):
        tool = DiffGeneratorTool()
        result = tool.run("hello", "hello")
        assert "No differences" in result

    def test_detect_diff(self):
        tool = DiffGeneratorTool()
        result = tool.run("hello world", "hello there")
        assert "-hello world" in result
        assert "+hello there" in result

    def test_custom_filenames(self):
        tool = DiffGeneratorTool()
        result = tool.run("old", "new", from_file="v1", to_file="v2")
        assert "v1" in result
        assert "v2" in result


class TestImageMetadataTool:
    def test_file_not_found(self):
        tool = ImageMetadataTool()
        result = tool.run("/nonexistent.png")
        assert "not found" in result.lower()

    def test_png_header(self, tmp_path):
        png = tmp_path / "test.png"
        png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + b"\x00\x00\x00\x10\x00\x00\x00\x10")
        tool = ImageMetadataTool()
        result = tool.run(str(png))
        assert "PNG" in result
        assert "16x16" in result


class TestCSVTool:
    def test_parse(self):
        tool = CSVTool()
        csv_data = "name,age\nAlice,30\nBob,25"
        result = tool.run(csv_data)
        assert "2 rows" in result
        assert "columns" in result.lower()

    def test_to_json(self):
        tool = CSVTool()
        csv_data = "name,age\nAlice,30"
        result = tool.run(csv_data, action="to_json")
        data = json.loads(result)
        assert data[0]["name"] == "Alice"

    def test_from_json(self):
        tool = CSVTool()
        json_data = '[{"name":"Alice","age":30}]'
        result = tool.run(json_data, action="from_json")
        assert "name,age" in result
        assert "Alice" in result

    def test_validate(self):
        tool = CSVTool()
        csv_data = "a,b,c\n1,2,3\n4,5,6"
        result = tool.run(csv_data, action="validate")
        assert "valid" in result.lower()

    def test_validate_bad(self):
        tool = CSVTool()
        csv_data = "a,b,c\n1,2,3\n4,5"
        result = tool.run(csv_data, action="validate")
        assert "wrong column count" in result


class TestXMLTool:
    def test_parse(self):
        tool = XMLTool()
        xml = "<root><item id='1'>Hello</item></root>"
        result = tool.run(xml)
        assert "<root>" in result
        assert "<item" in result

    def test_find(self):
        tool = XMLTool()
        xml = "<root><item>A</item><item>B</item></root>"
        result = tool.run(xml, action="find", xpath="item")
        assert "2 element" in result

    def test_validate(self):
        tool = XMLTool()
        xml = "<root></root>"
        result = tool.run(xml, action="validate")
        assert "Valid XML" in result

    def test_stats(self):
        tool = XMLTool()
        xml = "<root><a><b/></a></root>"
        result = tool.run(xml, action="stats")
        assert "elements" in result.lower()

    def test_invalid_xml(self):
        tool = XMLTool()
        result = tool.run("<root><unclosed>")
        assert "parse error" in result.lower()


class TestAPITesterTool:
    def test_blocked_localhost(self):
        tool = APITesterTool()
        result = tool.run("http://localhost:8080/api")
        assert "blocked" in result.lower()

    def test_blocked_metadata(self):
        tool = APITesterTool()
        result = tool.run("http://169.254.169.254/latest")
        assert "blocked" in result.lower()

    def test_invalid_method(self):
        tool = APITesterTool()
        result = tool.run("https://example.com", method="HACK")
        assert "Unsupported method" in result


class TestHashTool:
    def test_sha256(self):
        tool = HashTool()
        result = tool.run("hello", algorithm="sha256")
        assert "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824" in result

    def test_md5(self):
        tool = HashTool()
        result = tool.run("hello", algorithm="md5")
        assert "5d41402abc4b2a76b9719d911017c592" in result

    def test_unsupported_algo(self):
        tool = HashTool()
        result = tool.run("test", algorithm="blake2")
        assert "Unsupported" in result

    def test_file_not_found(self):
        tool = HashTool()
        result = tool.run("/nonexistent", algorithm="sha256", is_file=True)
        assert "not found" in result.lower()


class TestBase64Tool:
    def test_encode(self):
        tool = Base64Tool()
        result = tool.run("Hello World")
        assert "SGVsbG8gV29ybGQ=" in result

    def test_decode(self):
        tool = Base64Tool()
        result = tool.run("SGVsbG8gV29ybGQ=", action="decode")
        assert "Hello World" in result


class TestDateTool:
    def test_now(self):
        tool = DateTool()
        result = tool.run("now")
        assert "Current UTC" in result
        assert "ISO 8601" in result

    def test_parse(self):
        tool = DateTool()
        result = tool.run("parse", date1="2026-05-07")
        assert "Wednesday" in result or "Parsed:" in result

    def test_diff(self):
        tool = DateTool()
        result = tool.run("diff", date1="2026-01-01", date2="2026-01-05")
        assert "4 days" in result

    def test_format(self):
        tool = DateTool()
        result = tool.run("format", date1="2026-05-07")
        assert "2026-05-07" in result


class TestMarkdownTool:
    def test_to_html(self):
        tool = MarkdownTool()
        result = tool.run("# Hello\n\n**bold** and *italic*\n\n- item1\n- item2")
        assert "<h1>Hello</h1>" in result
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result
        assert "<li>item1</li>" in result

    def test_headings(self):
        tool = MarkdownTool()
        result = tool.run("# H1\n## H2\n### H3", action="headings")
        assert "H1: H1" in result
        assert "H2: H2" in result

    def test_links(self):
        tool = MarkdownTool()
        result = tool.run("[Google](https://google.com)", action="links")
        assert "Google" in result
        assert "https://google.com" in result

    def test_stats(self):
        tool = MarkdownTool()
        md = "# Title\nSome text here.\n\n- list item\n\n```python\nprint('hi')\n```"
        result = tool.run(md, action="stats")
        assert "Words:" in result
        assert "Code blocks: 1" in result


class TestGetAgentTools:
    def test_researcher_tools(self):
        tools = get_agent_tools("researcher")
        names = [t.name for t in tools]
        assert "web_search" in names
        assert "markdown_tool" in names

    def test_coder_tools(self):
        tools = get_agent_tools("coder")
        names = [t.name for t in tools]
        assert "code_executor" in names
        assert "diff_generator" in names
        assert "regex_tester" in names

    def test_analyst_tools(self):
        tools = get_agent_tools("analyst")
        names = [t.name for t in tools]
        assert "json_formatter" in names
        assert "csv_tool" in names
        assert "calculator" in names

    def test_security_tools(self):
        tools = get_agent_tools("security")
        names = [t.name for t in tools]
        assert "cve_search" in names
        assert "hash_tool" in names
        assert "api_tester" in names

    def test_writer_tools(self):
        tools = get_agent_tools("writer")
        names = [t.name for t in tools]
        assert "markdown_tool" in names
        assert "base64_tool" in names

    def test_general_tools(self):
        tools = get_agent_tools("general")
        names = [t.name for t in tools]
        assert "calculator" in names
        assert "date_tool" in names

    def test_unknown_agent_type(self):
        tools = get_agent_tools("unknown_type")
        assert len(tools) == 1
        assert tools[0].name == "rag_search"
