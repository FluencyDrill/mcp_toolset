"""Schemas for knowledge-base keyword search results.

Search returns compact hits (truncated snippets + metadata), never full documents, so
results stay small in the model's context.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchHit(BaseModel):
    """A single search result."""

    document_id: str
    score: float | None = Field(default=None, description="Retriever relevance score.")
    title: str | None = None
    url: str | None = None
    path: str | None = Field(default=None, description="On-disk path of the full content.")
    source: str | None = Field(default=None, description="Originating source, if recorded.")
    snippet: str = Field(description="Truncated content excerpt.")


class SearchResults(BaseModel):
    """The result of a knowledge-base search."""

    query: str
    hits: list[SearchHit] = Field(default_factory=list)
