"""Hayhooks wrapper deploying the text-statistics pipeline as a REST + MCP tool.

The wrapper folder name (``text_stats``) becomes the tool name, the ``run_api``
docstring becomes the tool description, and ``run_api``'s type-hinted arguments become
the tool's input schema.
"""

from hayhooks import BasePipelineWrapper

from mcp_toolset.pipelines import build_text_stats_pipeline
from mcp_toolset.schemas import TextStats


class PipelineWrapper(BasePipelineWrapper):
    def setup(self) -> None:
        self.pipeline = build_text_stats_pipeline()

    def run_api(self, text: str) -> dict:
        """Compute basic statistics (characters, words, sentences, reading time) for text."""
        result = self.pipeline.run({"stats": {"text": text}})
        return TextStats(**result["stats"]).model_dump()
