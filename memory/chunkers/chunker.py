"""Document chunking strategies for RAG memory system."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Chunk:
    """A single chunk of text with metadata."""

    text: str
    metadata: dict = field(default_factory=dict)
    chunk_id: str | None = None
    start_char: int = 0
    end_char: int = 0
    token_count: int = 0


class BaseChunker(ABC):
    """Base chunker interface."""

    @abstractmethod
    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        """Split text into chunks."""


class FixedSizeChunker(BaseChunker):
    """Split text into fixed-size chunks with overlap."""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separators: list[str] | None = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        chunks = []
        if not text:
            return chunks

        chunks_data = self._split_text(text)

        for i, chunk_text in enumerate(chunks_data):
            chunk = Chunk(
                text=chunk_text,
                metadata=metadata or {},
                chunk_id=f"chunk-{i}",
                token_count=len(chunk_text.split()),
            )
            chunks.append(chunk)

        return chunks

    def _split_text(self, text: str) -> list[str]:
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            if end >= len(text):
                chunks.append(text[start:])
                break

            split_pos = self._find_best_split(text[start:end])
            actual_end = start + split_pos

            chunks.append(text[start:actual_end])
            start = actual_end - self.chunk_overlap

            if start >= end:
                start = end

        return chunks

    def _find_best_split(self, segment: str) -> int:
        for sep in self.separators:
            idx = segment.rfind(sep)
            if idx > 0:
                return idx
        return len(segment)


class SemanticChunker(BaseChunker):
    """Split text based on semantic boundaries (paragraphs, headings)."""

    def __init__(
        self,
        min_chunk_size: int = 100,
        max_chunk_size: int = 1000,
    ):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        chunks = []
        if not text:
            return chunks

        sections = self._extract_sections(text)

        if len(sections) > 1:
            for header, content in sections:
                if content:
                    chunks.append(
                        Chunk(
                            text=content.strip(),
                            metadata={**(metadata or {}), "section": header},
                            token_count=len(content.split()),
                        )
                    )
        else:
            current_chunk = ""
            current_section_header = ""

            for header, content in sections:
                if header:
                    current_section_header = header

                if len(current_chunk) + len(content) > self.max_chunk_size:
                    if current_chunk:
                        chunks.append(
                            Chunk(
                                text=current_chunk.strip(),
                                metadata={**(metadata or {}), "section": current_section_header},
                                token_count=len(current_chunk.split()),
                            )
                        )
                    current_chunk = content
                else:
                    current_chunk += "\n" + content if current_chunk else content

            if current_chunk:
                chunks.append(
                    Chunk(
                        text=current_chunk.strip(),
                        metadata={**(metadata or {}), "section": current_section_header},
                        token_count=len(current_chunk.split()),
                    )
                )

        return chunks

    def _extract_sections(self, text: str) -> list[tuple[str, str]]:
        sections = []
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        matches = list(heading_pattern.finditer(text))

        if not matches:
            return [("", text)]

        for i, match in enumerate(matches):
            header = match.group(2)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sections.append((header, text[start:end].strip()))

        return sections


class MarkdownChunker(BaseChunker):
    """Chunk markdown documents preserving structure."""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        self.fixed_chunker = FixedSizeChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        code_blocks = self._extract_code_blocks(text)
        text_without_code = self._remove_code_blocks(text)

        chunks = self.fixed_chunker.chunk(text_without_code, metadata)

        for code_block in code_blocks:
            code_meta = {**(metadata or {}), "type": "code_block", "language": code_block.get("language", "")}
            chunk = Chunk(
                text=code_block["content"],
                metadata=code_meta,
                token_count=len(code_block["content"].split()),
            )
            chunks.append(chunk)

        return chunks

    def _extract_code_blocks(self, text: str) -> list[dict]:
        pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
        blocks = []
        for match in pattern.finditer(text):
            blocks.append(
                {
                    "language": match.group(1) or "text",
                    "content": match.group(0),
                }
            )
        return blocks

    def _remove_code_blocks(self, text: str) -> str:
        return re.sub(r"```\w*\n.*?```", "[CODE_BLOCK]", text, flags=re.DOTALL)


def create_chunker(
    strategy: str = "fixed",
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    min_chunk_size: int = 100,
    max_chunk_size: int = 1000,
) -> BaseChunker:
    """Factory function to create chunkers by strategy name."""
    strategies = {
        "fixed": lambda: FixedSizeChunker(chunk_size, chunk_overlap),
        "semantic": lambda: SemanticChunker(min_chunk_size, max_chunk_size),
        "markdown": lambda: MarkdownChunker(chunk_size, chunk_overlap),
    }

    if strategy not in strategies:
        raise ValueError(f"Unknown chunking strategy: {strategy}. Choose from {list(strategies.keys())}")

    return strategies[strategy]()
