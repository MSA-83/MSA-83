"""Summarizer agent executor."""

from typing import Optional

from agents.executors.base import BaseExecutor, ExecutorStatus, TaskResult


class SummarizerExecutor(BaseExecutor):
    """Execute text summarization tasks."""

    def __init__(self):
        super().__init__(
            name="summarizer",
            description="Summarize long documents, articles, or conversations",
        )

    def validate_input(self, task_input: str) -> bool:
        """Validate input for summarization."""
        return bool(task_input.strip()) and len(task_input) <= 10000

    async def execute(
        self,
        task_input: str,
        context: Optional[dict] = None,
    ) -> TaskResult:
        """Execute summarization task."""
        length = context.get("length", "medium") if context else "medium"
        format_type = context.get("format", "paragraph") if context else "paragraph"

        length_instructions = {
            "short": "Create a brief summary in 1-2 sentences.",
            "medium": "Create a concise summary in 3-5 sentences covering key points.",
            "long": "Create a detailed summary capturing all major points and nuances.",
        }

        format_instructions = {
            "paragraph": "Format as a single coherent paragraph.",
            "bullets": "Format as bullet points highlighting key takeaways.",
            "executive": "Format as an executive summary with sections: Overview, Key Findings, Recommendations.",
        }

        system_prompt = (
            "You are an expert summarizer. Extract the most important information "
            "from the provided text while maintaining accuracy and context.\n\n"
            f"{length_instructions.get(length, length_instructions['medium'])}\n"
            f"{format_instructions.get(format_type, format_instructions['paragraph'])}"
        )

        summary_text = (
            f"Summary ({length}, {format_type}):\n\n"
            f"[AI-generated summary would appear here in production with LLM]\n\n"
            f"Original length: {len(task_input)} characters\n"
            f"Key topics: {self._extract_keywords(task_input)}"
        )

        return TaskResult(
            status=ExecutorStatus.COMPLETED,
            output=summary_text,
            metadata={
                "original_length": len(task_input),
                "summary_length": len(summary_text),
                "compression_ratio": round(len(summary_text) / max(len(task_input), 1), 2),
                "length_mode": length,
                "format_mode": format_type,
            },
        )

    def _extract_keywords(self, text: str) -> str:
        """Extract top keywords from text."""
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "shall", "can", "need", "dare", "ought",
            "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after", "above", "below",
            "between", "out", "off", "over", "under", "again", "further", "then",
            "once", "here", "there", "when", "where", "why", "how", "all", "both",
            "each", "few", "more", "most", "other", "some", "such", "no", "nor",
            "not", "only", "own", "same", "so", "than", "too", "very", "just",
            "and", "but", "if", "or", "because", "until", "while", "this", "that",
            "these", "those", "it", "its", "i", "me", "my", "we", "our", "you",
            "your", "he", "him", "his", "she", "her", "they", "them", "their",
            "what", "which", "who", "whom",
        }

        words = text.lower().split()
        word_freq = {}
        for word in words:
            cleaned = "".join(c for c in word if c.isalnum())
            if cleaned and cleaned not in stop_words and len(cleaned) > 2:
                word_freq[cleaned] = word_freq.get(cleaned, 0) + 1

        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return ", ".join(word for word, _ in sorted_words[:5])


summarizer_executor = SummarizerExecutor()
