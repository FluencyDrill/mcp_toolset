"""Pipeline roundtrip test for the YouTube transcript pipeline (network mocked)."""

from __future__ import annotations

import pytest
from haystack.document_stores.in_memory import InMemoryDocumentStore

from mcp_toolset.custom_components import youtube_transcript as yt
from mcp_toolset.pipelines import build_youtube_transcript_pipeline

SEGMENTS = [
    {"text": "Hello world.", "start": 0.0, "duration": 1.5},
    {"text": "This is Haystack.", "start": 1.5, "duration": 2.0},
]


@pytest.fixture
def offline_youtube(monkeypatch):
    """Replace the network-touching helpers with deterministic stand-ins."""
    monkeypatch.setattr(yt, "_fetch_segments", lambda video_id: (SEGMENTS, "en"))
    monkeypatch.setattr(yt, "_fetch_title", lambda video_id: "Mock Title")


def test_youtube_pipeline_roundtrip(tmp_path, offline_youtube):
    store = InMemoryDocumentStore()
    pipeline = build_youtube_transcript_pipeline(store, content_dir=tmp_path)

    result = pipeline.run({"fetcher": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}})
    archived = result["archiver"]

    # Confirmation handle points at the stored document and the on-disk file.
    assert archived["document_id"] == "dQw4w9WgXcQ"
    assert archived["metadata"]["video_id"] == "dQw4w9WgXcQ"
    assert archived["metadata"]["title"] == "Mock Title"
    assert archived["metadata"]["language"] == "en"
    assert archived["metadata"]["word_count"] == 5

    saved = tmp_path / "dQw4w9WgXcQ.md"
    assert saved.exists()
    assert saved.read_text().startswith("# Mock Title")
    assert "Hello world. This is Haystack." in saved.read_text()

    # Store holds one small metadata doc, not the transcript text.
    assert store.count_documents() == 1
