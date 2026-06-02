"""Hayhooks wrapper deploying the YouTube transcript pipeline as a REST + MCP tool."""

from hayhooks import BasePipelineWrapper

from mcp_toolset.pipelines import build_youtube_transcript_pipeline
from mcp_toolset.schemas import ArchiveResult
from mcp_toolset.stores import get_document_store


class PipelineWrapper(BasePipelineWrapper):
    def setup(self) -> None:
        self.pipeline = build_youtube_transcript_pipeline(get_document_store())

    def run_api(self, url: str) -> dict:
        """Fetch a YouTube video's transcript, save it as markdown on disk, and record its
        metadata in the document store.

        Returns a small confirmation (document id, name, file path, and metadata) — not
        the transcript text itself, which stays in the saved markdown file.
        """
        result = self.pipeline.run({"fetcher": {"url": url}})
        return ArchiveResult(**result["archiver"]).model_dump()
