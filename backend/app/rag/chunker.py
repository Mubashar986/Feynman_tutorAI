from dataclasses import dataclass, field
import json
import re
from typing import Dict, List, Optional, Tuple


@dataclass
class ChunkPayload:
    """In-memory representation of a segmented text chunk."""
    content: str
    clean_content: str
    chunk_index: int
    page_number: int = 1
    token_count: int = 0
    heading_breadcrumbs: List[str] = field(default_factory=list)


class SemanticRecursiveChunker:
    """
    Pedagogical semantic text chunker preserving markdown heading hierarchy,
    sliding window overlap, and atomic LaTeX equation boundaries (ADR-018, FR-008).
    """

    def __init__(
        self,
        target_tokens: int = 512,
        overlap_tokens: int = 75,
        chars_per_token: float = 4.0,
    ):
        self.target_chars = int(target_tokens * chars_per_token)
        self.overlap_chars = int(overlap_tokens * chars_per_token)
        self.chars_per_token = chars_per_token

        # Separator hierarchy
        self.separators = [
            "\n## ",
            "\n### ",
            "\n#### ",
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ]

    def _protect_math_blocks(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Extracts multi-line ($$...$$ or \\[...\\]) and inline (\\(...\\) or $...$) LaTeX blocks,
        replacing them with safe placeholders to prevent formula truncation.
        """
        math_map: Dict[str, str] = {}
        counter = 0

        # 1. Display math blocks: $$...$$ or \[...\]
        def replace_display_math(match):
            nonlocal counter
            key = f"__MATH_DISPLAY_BLOCK_{counter}__"
            math_map[key] = match.group(0)
            counter += 1
            return key

        # Match $$...$$ across multiple lines or \[...\]
        text = re.sub(r"\$\$.*?\$\$", replace_display_math, text, flags=re.DOTALL)
        text = re.sub(r"\\\[.*?\\\]", replace_display_math, text, flags=re.DOTALL)

        # 2. Inline math blocks: \(...\) or $...$
        def replace_inline_math(match):
            nonlocal counter
            key = f"__MATH_INLINE_BLOCK_{counter}__"
            math_map[key] = match.group(0)
            counter += 1
            return key

        text = re.sub(r"\\\((.*?)\\\)", replace_inline_math, text)
        # Match single $...$ on single line (avoiding literal currency)
        text = re.sub(r"(?<!\\)\$(?!\s)([^\$\n]+?)(?<!\s)\$", replace_inline_math, text)

        return text, math_map

    def _restore_math_blocks(self, text: str, math_map: Dict[str, str]) -> str:
        """Restores protected math placeholders to their original LaTeX string."""
        for key, original in math_map.items():
            text = text.replace(key, original)
        return text

    def _estimate_tokens(self, text: str) -> int:
        """Estimates token count using character length ratio (~4 chars per token)."""
        return max(1, int(len(text) / self.chars_per_token))

    def _split_text_recursively(self, text: str, separators: List[str]) -> List[str]:
        """Recursively breaks text using the separator hierarchy until segments fit target_chars."""
        if not separators:
            # Fallback: slice into target_chars windows
            chunks = []
            for i in range(0, len(text), self.target_chars - self.overlap_chars):
                chunks.append(text[i : i + self.target_chars])
            return chunks

        sep = separators[0]
        splits = text.split(sep)
        result = []
        current_chunk = ""

        for part in splits:
            part_text = f"{part}{sep}" if sep != "" else part
            if len(current_chunk) + len(part_text) <= self.target_chars:
                current_chunk += part_text
            else:
                if current_chunk:
                    result.append(current_chunk.strip())
                if len(part_text) > self.target_chars:
                    # Recursive split on next separator
                    sub_chunks = self._split_text_recursively(part_text, separators[1:])
                    result.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = part_text

        if current_chunk.strip():
            result.append(current_chunk.strip())

        return result

    def chunk_document_text(
        self,
        raw_text: str,
        page_number: int = 1,
        initial_breadcrumbs: Optional[List[str]] = None,
    ) -> List[ChunkPayload]:
        """
        Splits document text into semantic chunks, preserving heading breadcrumbs and LaTeX math.
        """
        if not raw_text or not raw_text.strip():
            return []

        # 1. Protect math formulas
        masked_text, math_map = self._protect_math_blocks(raw_text)

        # 2. Parse sections and track heading breadcrumbs
        lines = masked_text.split("\n")
        sections: List[Tuple[List[str], str]] = []  # (breadcrumbs, section_text)
        current_headings: List[str] = list(initial_breadcrumbs or [])
        current_section_lines: List[str] = []

        for line in lines:
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
            if heading_match:
                # Save previous section if exists
                if current_section_lines:
                    sections.append((list(current_headings), "\n".join(current_section_lines)))
                    current_section_lines = []

                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                # Adjust breadcrumbs stack to current heading level
                if level <= len(current_headings):
                    current_headings = current_headings[: level - 1]
                current_headings.append(title)
            else:
                current_section_lines.append(line)

        if current_section_lines:
            sections.append((list(current_headings), "\n".join(current_section_lines)))

        # 3. Chunk each section recursively
        chunks: List[ChunkPayload] = []
        chunk_idx = 0

        for breadcrumbs, section_body in sections:
            if not section_body.strip():
                continue

            raw_chunks = self._split_text_recursively(section_body, self.separators)

            for raw_chunk in raw_chunks:
                # Restore math in chunk
                clean_chunk_text = self._restore_math_blocks(raw_chunk, math_map)
                clean_breadcrumbs = [self._restore_math_blocks(b, math_map) for b in breadcrumbs]

                # Format enriched content with breadcrumb context header
                if clean_breadcrumbs:
                    context_header = f"[Context: {' > '.join(clean_breadcrumbs)}]\n\n"
                    enriched_content = f"{context_header}{clean_chunk_text}"
                else:
                    enriched_content = clean_chunk_text

                token_cnt = self._estimate_tokens(enriched_content)

                payload = ChunkPayload(
                    content=enriched_content,
                    clean_content=clean_chunk_text,
                    chunk_index=chunk_idx,
                    page_number=page_number,
                    token_count=token_cnt,
                    heading_breadcrumbs=clean_breadcrumbs,
                )
                chunks.append(payload)
                chunk_idx += 1

        return chunks
