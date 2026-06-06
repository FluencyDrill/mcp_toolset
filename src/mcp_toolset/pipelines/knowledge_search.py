"""Knowledge-base keyword search pipeline.

A single backend-appropriate keyword retriever (Postgres full-text or in-memory BM25).
No embeddings, no models, no LLM — it returns matching documents for Claude to reason
over. The wrapper trims results into compact snippets before they reach the model.
"""

from __future__ import annotations

from haystack import Pipeline
from haystack.document_stores.types import DocumentStore

from mcp_toolset.stores import get_keyword_retriever


def build_knowledge_search_pipeline(document_store: DocumentStore) -> Pipeline:
    """Build a one-component keyword-search pipeline over ``document_store``."""
    pipeline = Pipeline()
    pipeline.add_component("retriever", get_keyword_retriever(document_store))
    return pipeline
