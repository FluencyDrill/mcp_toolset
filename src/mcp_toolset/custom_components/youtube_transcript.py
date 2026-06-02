"""Fetch a YouTube transcript (captions only) and render it as markdown.

Uses ``youtube-transcript-api`` (no audio download, no Whisper). The network-touching
code is isolated in :meth:`YouTubeTranscriptFetcher.run`; :func:`to_markdown` and
:func:`extract_video_id` are pure and unit-tested without network access.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any

from haystack import component

# Accepts full watch URLs, youtu.be short links, /embed/ and /shorts/ paths, or a raw id.
_VIDEO_ID_RE = re.compile(r"(?:v=|/embed/|/shorts/|youtu\.be/)([0-9A-Za-z_-]{11})")
_RAW_ID_RE = re.compile(r"^[0-9A-Za-z_-]{11}$")


def extract_video_id(url: str) -> str:
    """Extract an 11-character YouTube video id from a URL (or pass through a raw id)."""
    url = url.strip()
    if _RAW_ID_RE.match(url):
        return url
    match = _VIDEO_ID_RE.search(url)
    if not match:
        raise ValueError(f"Could not extract a YouTube video id from: {url!r}")
    return match.group(1)


def _format_timestamp(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"


def to_markdown(
    segments: list[dict],
    title: str | None = None,
    *,
    include_timestamps: bool = False,
) -> str:
    """Render transcript ``segments`` (dicts with ``text`` and ``start``) as markdown."""
    lines: list[str] = []
    if title:
        lines.append(f"# {title}\n")
    if include_timestamps:
        for seg in segments:
            text = str(seg.get("text", "")).strip()
            if not text:
                continue
            lines.append(f"- `[{_format_timestamp(seg.get('start', 0))}]` {text}")
    else:
        joined = " ".join(str(seg.get("text", "")).strip() for seg in segments)
        lines.append(re.sub(r"\s+", " ", joined).strip())
    return "\n".join(lines).strip() + "\n"


def _plain_text(segments: list[dict]) -> str:
    return re.sub(r"\s+", " ", " ".join(str(seg.get("text", "")) for seg in segments)).strip()


def _fetch_segments(video_id: str) -> tuple[list[dict], str | None]:
    """Return ``(segments, language_code)`` for a video, across api versions."""
    from youtube_transcript_api import YouTubeTranscriptApi

    # youtube-transcript-api >= 1.0 uses an instance ``fetch`` API.
    try:
        fetched = YouTubeTranscriptApi().fetch(video_id)
    except (AttributeError, TypeError):
        # Fall back to the <= 0.6 classmethod API.
        return YouTubeTranscriptApi.get_transcript(video_id), None
    return fetched.to_raw_data(), getattr(fetched, "language_code", None)


def _fetch_title(video_id: str) -> str | None:
    """Best-effort video title via the public oEmbed endpoint (network, may fail)."""
    params = urllib.parse.urlencode(
        {"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"}
    )
    try:
        with urllib.request.urlopen(f"https://www.youtube.com/oembed?{params}", timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8")).get("title")
    except Exception:
        return None


@component
class YouTubeTranscriptFetcher:
    """Fetch a YouTube transcript and emit markdown content plus metadata.

    Outputs are shaped to feed straight into :class:`MetadataArchiver`:
    ``content`` (markdown) is archived to disk, ``metadata`` is stored, and
    ``name``/``label`` identify the document.
    """

    def __init__(self, include_timestamps: bool = False) -> None:
        self.include_timestamps = include_timestamps

    @component.output_types(content=str, metadata=dict[str, Any], name=str, label=str)
    def run(self, url: str) -> dict:
        video_id = extract_video_id(url)
        segments, language = _fetch_segments(video_id)
        title = _fetch_title(video_id) or video_id

        content = to_markdown(segments, title=title, include_timestamps=self.include_timestamps)
        plain = _plain_text(segments)
        metadata = {
            "video_id": video_id,
            "title": title,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "language": language,
            "word_count": len(plain.split()),
            "char_count": len(plain),
            "fetched_at": datetime.now(UTC).isoformat(),
        }
        return {"content": content, "metadata": metadata, "name": video_id, "label": title}
