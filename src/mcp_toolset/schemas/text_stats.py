"""Schema for the text-statistics smoke-test pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TextStats(BaseModel):
    """Basic statistics about a piece of text."""

    characters: int = Field(description="Total number of characters.")
    words: int = Field(description="Number of whitespace-separated words.")
    sentences: int = Field(description="Approximate number of sentences.")
    reading_time_seconds: float = Field(
        description="Estimated reading time in seconds (at ~200 words/minute)."
    )
