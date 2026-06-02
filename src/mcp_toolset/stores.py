"""Shared document store(s).

Hayhooks loads every pipeline wrapper into the *same* process, so a module-level
cached store is shared across pipelines and across ``run_api`` calls. That lets one
pipeline write metadata that another (or a later request) can read back.

Swap :class:`InMemoryDocumentStore` for a persistent backend (e.g. Chroma, Qdrant,
pgvector) here and every pipeline picks it up without further changes.
"""

from __future__ import annotations

from functools import lru_cache

from haystack.document_stores.in_memory import InMemoryDocumentStore


@lru_cache(maxsize=1)
def get_document_store() -> InMemoryDocumentStore:
    """Return the process-wide shared document store (created once)."""
    return InMemoryDocumentStore()
