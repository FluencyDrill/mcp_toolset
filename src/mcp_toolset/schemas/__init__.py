"""Pydantic schemas for pipeline inputs/outputs.

These give pipeline wrappers typed, self-documenting return shapes. Hayhooks
serializes them to JSON for both the REST response and the MCP tool result.
"""

from mcp_toolset.schemas.archive_result import ArchiveResult, TranscriptMeta
from mcp_toolset.schemas.text_stats import TextStats

__all__ = ["ArchiveResult", "TranscriptMeta", "TextStats"]
