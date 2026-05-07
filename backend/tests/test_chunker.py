"""Tests for the chunking module."""

import pytest

from memory.chunkers.chunker import (
    FixedSizeChunker,
    MarkdownChunker,
    SemanticChunker,
    create_chunker,
)


class TestFixedSizeChunker:
    def test_basic_chunking(self):
        chunker = FixedSizeChunker(chunk_size=50, chunk_overlap=10)
        text = "This is a test document. " * 10
        chunks = chunker.chunk(text)

        assert len(chunks) > 1
        assert all(c.text for c in chunks)

    def test_empty_text(self):
        chunker = FixedSizeChunker()
        chunks = chunker.chunk("")
        assert len(chunks) == 0

    def test_single_chunk(self):
        chunker = FixedSizeChunker(chunk_size=500, chunk_overlap=50)
        text = "Short text"
        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_overlap(self):
        chunker = FixedSizeChunker(chunk_size=20, chunk_overlap=5)
        text = "A B C D E F G H I J K L M N O P"
        chunks = chunker.chunk(text)

        if len(chunks) > 1:
            last_end = chunks[0].text[-5:]
            assert last_end in chunks[1].text


class TestSemanticChunker:
    def test_heading_based_chunking(self):
        chunker = SemanticChunker()
        text = """# Introduction
This is the intro section with some content.

# Methods
Here are the methods we used.

# Results
The results show significant findings."""

        chunks = chunker.chunk(text)
        assert len(chunks) >= 2

    def test_no_headings(self):
        chunker = SemanticChunker()
        text = "Just plain text without headings."
        chunks = chunker.chunk(text)

        assert len(chunks) == 1

    def test_empty_text(self):
        chunker = SemanticChunker()
        chunks = chunker.chunk("")
        assert len(chunks) == 0


class TestMarkdownChunker:
    def test_code_block_extraction(self):
        chunker = MarkdownChunker()
        text = """Regular text here.

```python
def hello():
    print("Hello")
```

More text after."""

        chunks = chunker.chunk(text)

        code_chunks = [c for c in chunks if c.metadata.get("type") == "code_block"]
        assert len(code_chunks) == 1
        assert "python" in code_chunks[0].metadata.get("language", "")

    def test_empty_text(self):
        chunker = MarkdownChunker()
        chunks = chunker.chunk("")
        assert len(chunks) == 0


class TestCreateChunker:
    def test_fixed_strategy(self):
        chunker = create_chunker(strategy="fixed")
        assert isinstance(chunker, FixedSizeChunker)

    def test_semantic_strategy(self):
        chunker = create_chunker(strategy="semantic")
        assert isinstance(chunker, SemanticChunker)

    def test_markdown_strategy(self):
        chunker = create_chunker(strategy="markdown")
        assert isinstance(chunker, MarkdownChunker)

    def test_invalid_strategy(self):
        with pytest.raises(ValueError):
            create_chunker(strategy="invalid")
