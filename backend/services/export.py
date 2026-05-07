"""Export utilities for conversations and documents."""

import json
from datetime import datetime


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
