"""Hayhooks wrapper deploying keyword search over the knowledge store as an MCP tool."""

from hayhooks import BasePipelineWrapper

from mcp_toolset.pipelines import build_knowledge_search_pipeline
from mcp_toolset.schemas import SearchHit, SearchResults
from mcp_toolset.stores import get_document_store


class PipelineWrapper(BasePipelineWrapper):
    def setup(self) -> None:
        self.pipeline = build_knowledge_search_pipeline(get_document_store())

    def run_api(self, query: str, top_k: int = 5, max_chars: int = 500) -> dict:
        """Keyword-search the knowledge store (e.g. saved transcripts) and return the top
        matching documents as short snippets with their metadata.

        Returns up to ``top_k`` hits, each excerpt truncated to ``max_chars`` characters.
        Open a hit's ``path`` to read its full content. This does not call any LLM.
        """
        result = self.pipeline.run({"retriever": {"query": query, "top_k": top_k}})
        documents = result["retriever"]["documents"]

        hits = []
        for doc in documents:
            meta = doc.meta or {}
            content = doc.content or ""
            hits.append(
                SearchHit(
                    document_id=doc.id,
                    score=doc.score,
                    title=meta.get("title"),
                    url=meta.get("url"),
                    path=meta.get("path"),
                    source=meta.get("source"),
                    snippet=content[:max_chars],
                )
            )
        return SearchResults(query=query, hits=hits).model_dump()
