"""Reusable Haystack custom components.

- :class:`TextStatistics` — a tiny, dependency-free smoke-test component.
- :class:`YouTubeTranscriptFetcher` — fetches captions and renders markdown.
- :class:`MetadataArchiver` — GENERIC: durably persists content + metadata and
  returns a confirmation handle. Reuse it in any pipeline that needs to "save and
  confirm".
"""

from mcp_toolset.custom_components.metadata_archiver import MetadataArchiver
from mcp_toolset.custom_components.text_statistics import TextStatistics
from mcp_toolset.custom_components.youtube_transcript import (
    YouTubeTranscriptFetcher,
    to_markdown,
)

__all__ = [
    "MetadataArchiver",
    "TextStatistics",
    "YouTubeTranscriptFetcher",
    "to_markdown",
]
