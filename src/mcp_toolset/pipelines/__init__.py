"""Pipeline builder functions.

Each function constructs and returns a Haystack :class:`~haystack.Pipeline`. The thin
wrappers under ``pipeline_wrappers/`` import these to deploy the pipelines via Hayhooks.
"""

from mcp_toolset.pipelines.knowledge_search import build_knowledge_search_pipeline
from mcp_toolset.pipelines.text_stats import build_text_stats_pipeline
from mcp_toolset.pipelines.youtube_transcript import build_youtube_transcript_pipeline

__all__ = [
    "build_knowledge_search_pipeline",
    "build_text_stats_pipeline",
    "build_youtube_transcript_pipeline",
]
