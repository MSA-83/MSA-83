"""Agent memory management system."""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MemoryEntry:
    """A single memory entry."""

    content: str
    entry_type: str  # "conversation", "knowledge", "task_result", "observation"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)


class AgentMemory:
    """Per-agent memory system with short-term and long-term storage."""

    def __init__(
        self,
        agent_id: str,
        memory_dir: str = "./agent_memory",
        max_short_term: int = 50,
    ):
        self.agent_id = agent_id
        self.memory_dir = os.path.join(memory_dir, agent_id)
        self.max_short_term = max_short_term
        self._short_term: list[MemoryEntry] = []

        os.makedirs(self.memory_dir, exist_ok=True)

    def add(self, content: str, entry_type: str, metadata: dict | None = None):
        """Add an entry to memory."""
        entry = MemoryEntry(
            content=content,
            entry_type=entry_type,
            metadata=metadata or {},
        )

        self._short_term.append(entry)

        if len(self._short_term) > self.max_short_term:
            self._consolidate()

        self._persist_long_term(entry)

    def search(self, query: str, entry_type: str | None = None) -> list[MemoryEntry]:
        """Search memory for relevant entries."""
        results = []
        query_lower = query.lower()

        for entry in self._short_term:
            if entry_type and entry.entry_type != entry_type:
                continue
            if query_lower in entry.content.lower():
                results.append(entry)

        for entry in self._load_long_term():
            if entry_type and entry.entry_type != entry_type:
                continue
            if query_lower in entry.content.lower():
                results.append(entry)

        return results

    def get_recent(self, n: int = 10, entry_type: str | None = None) -> list[MemoryEntry]:
        """Get the most recent memory entries."""
        entries = self._short_term

        if entry_type:
            entries = [e for e in entries if e.entry_type == entry_type]

        return entries[-n:]

    def get_context(self, max_tokens: int = 4000) -> str:
        """Build context string from recent memory for LLM prompting."""
        entries = self.get_recent(20)

        context_parts = []
        total_tokens = 0

        for entry in reversed(entries):
            entry_text = f"[{entry.entry_type}] {entry.content}"
            entry_tokens = len(entry_text.split())

            if total_tokens + entry_tokens > max_tokens:
                break

            context_parts.insert(0, entry_text)
            total_tokens += entry_tokens

        return "\n\n".join(context_parts)

    def clear(self):
        """Clear all memory."""
        self._short_term = []
        long_term_file = os.path.join(self.memory_dir, "long_term.jsonl")
        if os.path.exists(long_term_file):
            os.remove(long_term_file)

    def get_stats(self) -> dict:
        """Get memory statistics."""
        long_term_count = len(self._load_long_term())

        return {
            "agent_id": self.agent_id,
            "short_term_entries": len(self._short_term),
            "long_term_entries": long_term_count,
            "total_entries": len(self._short_term) + long_term_count,
        }

    def _consolidate(self):
        """Move oldest short-term entries to long-term storage."""
        to_move = self._short_term[: len(self._short_term) // 2]
        self._short_term = self._short_term[len(self._short_term) // 2 :]

        for entry in to_move:
            self._persist_long_term(entry)

    def _persist_long_term(self, entry: MemoryEntry):
        """Append entry to long-term storage file."""
        long_term_file = os.path.join(self.memory_dir, "long_term.jsonl")

        with open(long_term_file, "a") as f:
            f.write(
                json.dumps(
                    {
                        "content": entry.content,
                        "entry_type": entry.entry_type,
                        "timestamp": entry.timestamp,
                        "metadata": entry.metadata,
                    }
                )
                + "\n"
            )

    def _load_long_term(self) -> list[MemoryEntry]:
        """Load entries from long-term storage."""
        long_term_file = os.path.join(self.memory_dir, "long_term.jsonl")

        if not os.path.exists(long_term_file):
            return []

        entries = []
        with open(long_term_file) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    entries.append(MemoryEntry(**data))

        return entries


class SharedMemory:
    """Shared memory across all agents in a crew."""

    def __init__(self, crew_id: str, memory_dir: str = "./agent_memory"):
        self.crew_id = crew_id
        self.memory_file = os.path.join(memory_dir, crew_id, "shared.jsonl")
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)

    def add(self, content: str, source_agent: str, metadata: dict | None = None):
        """Add an entry to shared memory."""
        entry = {
            "content": content,
            "source_agent": source_agent,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        with open(self.memory_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_all(self, limit: int = 100) -> list[dict]:
        """Get all shared memory entries."""
        if not os.path.exists(self.memory_file):
            return []

        entries = []
        with open(self.memory_file) as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))

        return entries[-limit:]

    def search(self, query: str) -> list[dict]:
        """Search shared memory."""
        entries = self.get_all()
        query_lower = query.lower()

        return [e for e in entries if query_lower in e["content"].lower()]
