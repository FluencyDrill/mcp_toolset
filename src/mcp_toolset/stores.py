"""Shared document store(s) and matching retrievers.

Hayhooks loads every pipeline wrapper into the *same* process, so a module-level cached
store is shared across pipelines and across ``run_api`` calls. That lets one pipeline
write content that another (or a later request) can search.

The backend is chosen by ``MCP_TOOLSET_STORE``:

- ``memory`` (default) — :class:`InMemoryDocumentStore`; zero-config, ephemeral.
- ``pgvector`` — :class:`PgvectorDocumentStore`; durable Postgres, connection from
  ``PG_CONN_STR``. Requires the ``postgres`` extra (``uv sync --extra postgres``).

``get_document_store()`` is the single swap point: every pipeline reads from it, so
switching backends is purely a matter of environment configuration.
"""

from __future__ import annotations

from functools import lru_cache

from haystack.document_stores.types import DocumentStore

from mcp_toolset import config


@lru_cache(maxsize=1)
def get_document_store() -> DocumentStore:
    """Return the process-wide shared document store (created once).

    Backend is selected by ``MCP_TOOLSET_STORE`` (``memory`` or ``pgvector``).
    """
    backend = config.store_backend()
    if backend == "pgvector":
        # Imported lazily so the base install (and offline tests) need not install pgvector.
        from haystack_integrations.document_stores.pgvector import PgvectorDocumentStore

        # Connection string is read from PG_CONN_STR by the store's default Secret.
        return PgvectorDocumentStore(
            table_name=config.pg_table(),
            language=config.DEFAULT_PG_LANGUAGE,
            recreate_table=False,
        )

    from haystack.document_stores.in_memory import InMemoryDocumentStore

    return InMemoryDocumentStore()


def get_keyword_retriever(store: DocumentStore):
    """Return a lexical (keyword) retriever matching the store backend.

    No embeddings or models are involved — Postgres full-text for the pgvector backend,
    in-memory BM25 otherwise. Selecting by store type keeps the search pipeline identical
    across backends and lets tests run fully offline.
    """
    if type(store).__name__ == "PgvectorDocumentStore":
        from haystack_integrations.components.retrievers.pgvector import (
            PgvectorKeywordRetriever,
        )

        return PgvectorKeywordRetriever(document_store=store)

    from haystack.components.retrievers.in_memory import InMemoryBM25Retriever

    return InMemoryBM25Retriever(document_store=store)
