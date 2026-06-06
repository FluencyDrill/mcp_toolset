"""A minimal custom component used as an offline smoke test.

It needs no network, no API keys, and no model downloads, which makes it the ideal
"does the MCP plumbing work end-to-end?" example.
"""

from __future__ import annotations

import re

from haystack import component

#: Words per minute used to estimate reading time.
_WORDS_PER_MINUTE = 200

_SENTENCE_BOUNDARY = re.compile(r"[.!?]+")


@component
class TextStatistics:
    """Compute basic statistics (characters, words, sentences, reading time) for text."""

    @component.output_types(characters=int, words=int, sentences=int, reading_time_seconds=float)
    def run(self, text: str) -> dict:
        words = text.split()
        word_count = len(words)
        sentences = [s for s in _SENTENCE_BOUNDARY.split(text) if s.strip()]
        reading_time = round(word_count / _WORDS_PER_MINUTE * 60, 2)
        return {
            "characters": len(text),
            "words": word_count,
            "sentences": len(sentences),
            "reading_time_seconds": reading_time,
        }
