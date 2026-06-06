"""YouTube transcript pipeline: fetch captions, archive markdown + metadata.

Two components only::

    YouTubeTranscriptFetcher  ->  MetadataArchiver

The fetcher renders captions to markdown and emits metadata; the archiver writes the
markdown to disk, stores the metadata document, and returns a confirmation handle.
``MetadataArchiver`` is the leaf component, so its outputs are the pipeline result.
"""

from __future__ import annotations

from pathlib import Path

from haystack import Pipeline
from haystack.document_stores.types import DocumentStore

from mcp_toolset.config import transcripts_dir
from mcp_toolset.custom_components import MetadataArchiver, YouTubeTranscriptFetcher


def build_youtube_transcript_pipeline(
    document_store: DocumentStore,
    content_dir: str | Path | None = None,
) -> Pipeline:
    """Build the fetch -> archive pipeline.

    :param document_store: store for the metadata document.
    :param content_dir: where transcript markdown is written (defaults to
        :func:`mcp_toolset.config.transcripts_dir`).
    """
    content_dir = content_dir if content_dir is not None else transcripts_dir()

    pipeline = Pipeline()
    pipeline.add_component("fetcher", YouTubeTranscriptFetcher())
    pipeline.add_component(
        "archiver",
        MetadataArchiver(document_store=document_store, content_dir=content_dir),
    )

    pipeline.connect("fetcher.content", "archiver.content")
    pipeline.connect("fetcher.metadata", "archiver.metadata")
    pipeline.connect("fetcher.name", "archiver.name")
    pipeline.connect("fetcher.label", "archiver.label")
    return pipeline
