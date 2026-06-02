"""Unit tests for the custom components (all offline, no YouTube network)."""

from __future__ import annotations

from haystack.document_stores.in_memory import InMemoryDocumentStore

from mcp_toolset.custom_components import MetadataArchiver, TextStatistics
from mcp_toolset.custom_components.youtube_transcript import extract_video_id, to_markdown

# Synthetic transcript segments shaped like youtube-transcript-api output.
SEGMENTS = [
    {"text": "Hello world.", "start": 0.0, "duration": 1.5},
    {"text": "This is\nHaystack.", "start": 1.5, "duration": 2.0},
]


def test_text_statistics():
    out = TextStatistics().run(text="Hello world. This is Haystack.")
    assert out["characters"] == len("Hello world. This is Haystack.")
    assert out["words"] == 5
    assert out["sentences"] == 2
    assert out["reading_time_seconds"] > 0


def test_extract_video_id():
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_to_markdown_prose():
    md = to_markdown(SEGMENTS, title="My Video")
    assert md.startswith("# My Video")
    # Whitespace (including the embedded newline) is collapsed into prose.
    assert "Hello world. This is Haystack." in md
    assert "\n\n" not in md.strip().split("# My Video\n", 1)[-1].strip()


def test_to_markdown_timestamps():
    md = to_markdown(SEGMENTS, title="My Video", include_timestamps=True)
    assert "`[0:00]`" in md
    assert "`[0:01]`" in md


def test_metadata_archiver_writes_file_and_store(tmp_path):
    store = InMemoryDocumentStore()
    archiver = MetadataArchiver(document_store=store, content_dir=tmp_path)

    out = archiver.run(
        content="# Title\n\nthe transcript body",
        metadata={"video_id": "abc123", "title": "Title"},
        name="abc123",
        label="Title",
    )

    # Confirmation handle.
    assert out["document_id"] == "abc123"
    assert out["document_name"] == "abc123"
    assert out["metadata"]["path"] == out["path"]

    # File written to disk with the full content.
    written = tmp_path / "abc123.md"
    assert written.exists()
    assert "the transcript body" in written.read_text()

    # Exactly one document in the store; by default it holds the searchable content,
    # with the title recorded in metadata.
    assert store.count_documents() == 1
    doc = store.filter_documents()[0]
    assert doc.id == "abc123"
    assert "the transcript body" in (doc.content or "")
    assert doc.meta["title"] == "Title"


def test_metadata_archiver_overwrites_on_rerun(tmp_path):
    store = InMemoryDocumentStore()
    archiver = MetadataArchiver(document_store=store, content_dir=tmp_path)
    meta = {"video_id": "abc123"}

    archiver.run(content="v1", metadata=meta, name="abc123")
    archiver.run(content="v2", metadata=meta, name="abc123")

    assert store.count_documents() == 1
    assert (tmp_path / "abc123.md").read_text() == "v2"


def test_metadata_archiver_metadata_only(tmp_path):
    store = InMemoryDocumentStore()
    archiver = MetadataArchiver(document_store=store, content_dir=None)

    out = archiver.run(content="ignored on disk", metadata={"k": "v"}, name="n1")

    assert out["path"] is None
    assert list(tmp_path.iterdir()) == []
    assert store.count_documents() == 1
