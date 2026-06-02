"""A generic, reusable component that durably persists content + metadata.

This is intentionally **not** tied to YouTube. Any pipeline can end with a
``MetadataArchiver`` to:

1. (optionally) write the ``content`` payload to a file on disk, and
2. write a lightweight metadata :class:`~haystack.Document` to a document store,

and get back a confirmation handle (``document_id``/``document_name``/``path``).

Why a custom component instead of the stock ``DocumentWriter``? ``DocumentWriter.run``
returns only ``{"documents_written": n}`` — it does not emit the stored document, so it
cannot hand the document id back as confirmation. This component writes to the store
itself and returns that id. As a leaf component, its outputs surface directly from
``pipeline.run()``.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

from haystack import Document, component
from haystack.document_stores.types import DocumentStore, DuplicatePolicy

_UNSAFE_FILENAME = re.compile(r"[^\w.-]+")


def _safe_stem(name: str) -> str:
    """Make ``name`` safe to use as a filename stem."""
    return _UNSAFE_FILENAME.sub("_", name).strip("_") or uuid.uuid4().hex


@component
class MetadataArchiver:
    """Persist content to disk and its metadata to a document store; return a handle.

    :param document_store: where the metadata document is written.
    :param content_dir: if set, ``content`` is written to ``<content_dir>/<name>.<ext>``
        and the resulting path is added to the metadata. If ``None``, nothing is written
        to disk (metadata-only).
    :param file_extension: extension for the on-disk content file.
    :param policy: duplicate policy for the store write (default OVERWRITE, so
        re-archiving the same ``name`` updates the existing document in place).
    """

    def __init__(
        self,
        document_store: DocumentStore,
        content_dir: str | Path | None = None,
        file_extension: str = ".md",
        policy: DuplicatePolicy = DuplicatePolicy.OVERWRITE,
    ) -> None:
        self.document_store = document_store
        self.content_dir = Path(content_dir) if content_dir is not None else None
        self.file_extension = file_extension
        self.policy = policy

    @component.output_types(document_id=str, document_name=str, path=str, metadata=dict)
    def run(
        self,
        content: str,
        metadata: dict[str, Any],
        name: str | None = None,
        label: str | None = None,
    ) -> dict:
        meta = dict(metadata)
        stem = _safe_stem(name) if name else uuid.uuid4().hex

        path: Path | None = None
        if self.content_dir is not None:
            self.content_dir.mkdir(parents=True, exist_ok=True)
            path = self.content_dir / f"{stem}{self.file_extension}"
            path.write_text(content, encoding="utf-8")
            meta["path"] = str(path)

        # Store a *small* document: the label (not the large content) plus metadata.
        # Pin the id to ``name`` when given so re-archiving overwrites cleanly.
        doc_kwargs: dict[str, Any] = {"content": label or name or stem, "meta": meta}
        if name:
            doc_kwargs["id"] = name
        doc = Document(**doc_kwargs)

        self.document_store.write_documents([doc], policy=self.policy)

        return {
            "document_id": doc.id,
            "document_name": name or doc.id,
            "path": str(path) if path is not None else None,
            "metadata": doc.meta,
        }
