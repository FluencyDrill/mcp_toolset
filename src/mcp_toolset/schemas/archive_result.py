"""Schema returned after archiving content + metadata.

This is the lightweight confirmation handed back to the LLM: it points at the stored
document and the on-disk file, without ever returning the (potentially large) content.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TranscriptMeta(BaseModel):
    """Metadata recorded for a fetched YouTube transcript."""

    video_id: str
    title: str | None = None
    url: str | None = None
    language: str | None = None
    word_count: int | None = None
    char_count: int | None = None
    fetched_at: str | None = Field(default=None, description="ISO-8601 UTC timestamp.")


class ArchiveResult(BaseModel):
    """Confirmation that content was durably archived.

    Returned by archiving pipelines so the caller knows *where* the content lives
    (store id + file path) without the content itself entering the context window.
    """

    document_id: str = Field(description="ID of the metadata document in the store.")
    document_name: str = Field(description="Human-friendly name/key for the document.")
    path: str | None = Field(
        default=None, description="Filesystem path of the saved content, if written to disk."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="The metadata stored alongside the document."
    )
