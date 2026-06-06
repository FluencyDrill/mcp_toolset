"""Offline tests for the store backend seam and keyword search pipeline."""

from __future__ import annotations

import importlib

from haystack import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore

from mcp_toolset.custom_components import MetadataArchiver
from mcp_toolset.pipelines import build_knowledge_search_pipeline


def _seed_store() -> InMemoryDocumentStore:
    store = InMemoryDocumentStore()
    store.write_documents(
        [
            Document(
                id="vid1",
                content="A deep discussion about Haystack pipelines and components.",
                meta={"title": "Haystack talk", "url": "u1", "path": "p1"},
            ),
            Document(
                id="vid2",
                content="A cooking show about making fresh pasta from scratch.",
                meta={"title": "Pasta", "url": "u2", "path": "p2"},
            ),
        ]
    )
    return store


def test_get_document_store_defaults_to_memory(monkeypatch):
    monkeypatch.delenv("MCP_TOOLSET_STORE", raising=False)
    import mcp_toolset.stores as stores

    importlib.reload(stores)  # reset the lru_cache
    store = stores.get_document_store()
    assert type(store).__name__ == "InMemoryDocumentStore"


def test_get_keyword_retriever_for_memory():
    from mcp_toolset.stores import get_keyword_retriever

    retriever = get_keyword_retriever(InMemoryDocumentStore())
    assert type(retriever).__name__ == "InMemoryBM25Retriever"


def test_knowledge_search_returns_relevant_doc():
    store = _seed_store()
    pipeline = build_knowledge_search_pipeline(store)

    result = pipeline.run({"retriever": {"query": "Haystack pipelines", "top_k": 1}})
    docs = result["retriever"]["documents"]

    assert len(docs) == 1
    assert docs[0].id == "vid1"
    assert docs[0].meta["title"] == "Haystack talk"


def test_knowledge_search_respects_top_k():
    store = _seed_store()
    pipeline = build_knowledge_search_pipeline(store)

    result = pipeline.run({"retriever": {"query": "show pasta Haystack", "top_k": 1}})
    assert len(result["retriever"]["documents"]) == 1


def test_archiver_stores_full_content_by_default(tmp_path):
    store = InMemoryDocumentStore()
    archiver = MetadataArchiver(document_store=store, content_dir=tmp_path)

    archiver.run(
        content="# Title\n\nsearchable transcript body",
        metadata={"video_id": "abc"},
        name="abc",
        label="Title",
    )

    doc = store.filter_documents()[0]
    assert "searchable transcript body" in doc.content
    assert doc.meta["title"] == "Title"
    assert (tmp_path / "abc.md").exists()


def test_archiver_label_only_when_store_content_false(tmp_path):
    store = InMemoryDocumentStore()
    archiver = MetadataArchiver(document_store=store, content_dir=tmp_path, store_content=False)

    archiver.run(
        content="big body that should NOT be in the store",
        metadata={"video_id": "abc"},
        name="abc",
        label="Title",
    )

    doc = store.filter_documents()[0]
    assert doc.content == "Title"
    assert "big body" not in (doc.content or "")
    # Full content is still on disk.
    assert "big body" in (tmp_path / "abc.md").read_text()
