"""Export utilities for conversations and documents."""

import json
from datetime import datetime

from weasyprint import HTML


class MarkdownExporter:
    """Export conversations and data as Markdown."""

    @staticmethod
    def export_conversation(
        conversation_title: str,
        messages: list[dict],
        include_metadata: bool = False,
    ) -> str:
        """Export a conversation as Markdown."""
        lines = [
            f"# {conversation_title}",
            "",
            f"*Exported on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*",
            "",
            "---",
            "",
        ]

        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            created = msg.get("created_at", "")

            if role == "user":
                lines.append("## You")
            elif role == "assistant":
                lines.append("## Titanium")
            else:
                lines.append(f"## {role.capitalize()}")

            if include_metadata and created:
                lines.append(f"*{created}*")

            lines.append("")
            lines.append(content)
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def export_memory_chunks(
        chunks: list[dict],
        source: str = "Memory Export",
    ) -> str:
        """Export memory chunks as Markdown."""
        lines = [
            f"# {source}",
            "",
            f"*Exported on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*",
            "",
            f"Total chunks: {len(chunks)}",
            "",
            "---",
            "",
        ]

        for i, chunk in enumerate(chunks, 1):
            lines.append(f"## Chunk {i}")

            if chunk.get("metadata"):
                meta = chunk["metadata"]
                if "source" in meta:
                    lines.append(f"**Source:** {meta['source']}")
                if "document_id" in meta:
                    lines.append(f"**Document:** {meta['document_id']}")

            lines.append("")
            lines.append(chunk.get("text", ""))
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)


class JSONExporter:
    """Export data as JSON."""

    @staticmethod
    def export_conversation(
        conversation_id: str,
        conversation_title: str,
        messages: list[dict],
    ) -> str:
        """Export a conversation as JSON."""
        data = {
            "conversation_id": conversation_id,
            "title": conversation_title,
            "exported_at": datetime.utcnow().isoformat(),
            "message_count": len(messages),
            "messages": messages,
        }

        return json.dumps(data, indent=2, ensure_ascii=False)

    @staticmethod
    def export_usage_report(
        user_id: str,
        usage_data: dict,
    ) -> str:
        """Export usage data as JSON report."""
        report = {
            "user_id": user_id,
            "generated_at": datetime.utcnow().isoformat(),
            "usage": usage_data,
        }

        return json.dumps(report, indent=2, ensure_ascii=False)


class CSVExporter:
    """Export data as CSV."""

    @staticmethod
    def export_conversation(messages: list[dict]) -> str:
        """Export conversation as CSV."""
        lines = ["role,content,created_at"]

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "").replace('"', '""').replace("\n", "\\n")
            created = msg.get("created_at", "")
            lines.append(f'"{role}","{content}","{created}"')

        return "\n".join(lines)


def export_to_file(content: str, filename: str, format: str = "md"):
    """Helper to write export content to a file."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)


class PDFExporter:
    """Export conversations to styled PDF documents."""

    @staticmethod
    def export_conversation(
        title: str,
        messages: list[dict],
        include_metadata: bool = False,
    ) -> bytes:
        """Export a conversation to a styled PDF."""
        message_rows = ""
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            ts = msg.get("created_at", "")
            model = msg.get("model", "")

            role_class = "user" if role == "user" else "assistant"
            meta_html = ""
            if include_metadata and (ts or model):
                meta_parts = []
                if ts:
                    meta_parts.append(f"Time: {ts}")
                if model:
                    meta_parts.append(f"Model: {model}")
                meta_html = f'<div class="meta">{", ".join(meta_parts)}</div>'

            content_escaped = content.replace("<", "&lt;").replace(">", "&gt;")
            message_rows += f"""
            <div class="message {role_class}">
                <div class="role-label">{role.upper()}</div>
                <div class="content">{content_escaped}</div>
                {meta_html}
            </div>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{ size: A4; margin: 2cm; @bottom-right {{ content: "Page " counter(page) " of " counter(pages); font-size: 9pt; color: #666; }} }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 11pt; line-height: 1.6; color: #1a1a2e; }}
                .header {{ text-align: center; padding-bottom: 1cm; border-bottom: 2px solid #4a90d9; margin-bottom: 1cm; }}
                .header h1 {{ font-size: 22pt; color: #1a1a2e; margin: 0 0 0.3cm 0; }}
                .header .date {{ color: #666; font-size: 10pt; }}
                .header .stats {{ margin-top: 0.3cm; font-size: 10pt; color: #4a90d9; }}
                .message {{ margin-bottom: 0.5cm; padding: 0.4cm; border-radius: 4px; page-break-inside: avoid; }}
                .message.user {{ background-color: #f0f4ff; border-left: 3px solid #4a90d9; }}
                .message.assistant {{ background-color: #f8f9fa; border-left: 3px solid #28a745; }}
                .role-label {{ font-size: 8pt; font-weight: bold; color: #666; margin-bottom: 0.2cm; text-transform: uppercase; letter-spacing: 0.5pt; }}
                .content {{ white-space: pre-wrap; word-wrap: break-word; }}
                .meta {{ font-size: 8pt; color: #999; margin-top: 0.2cm; }}
                .footer {{ text-align: center; font-size: 8pt; color: #999; margin-top: 1cm; border-top: 1px solid #ddd; padding-top: 0.3cm; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                <div class="date">Exported: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}</div>
                <div class="stats">{len(messages)} messages</div>
            </div>
            {message_rows}
            <div class="footer">Exported from Titanium Enterprise AI Platform</div>
        </body>
        </html>
        """

        return HTML(string=html_content).write_pdf()
