"""Runtime configuration helpers for mcp_toolset.

Keep configuration in one place so components and pipelines read the same values.
"""

from __future__ import annotations

import os
from pathlib import Path

#: Default directory (relative to the working directory) where transcripts are stored.
DEFAULT_TRANSCRIPTS_DIR = "./data/transcripts"

#: Environment variable that overrides the transcripts directory.
TRANSCRIPTS_DIR_ENV = "MCP_TOOLSET_TRANSCRIPTS_DIR"

#: Environment variable selecting the document store backend ("memory" or "pgvector").
STORE_BACKEND_ENV = "MCP_TOOLSET_STORE"

#: Environment variable holding the Postgres table name for the pgvector backend.
PG_TABLE_ENV = "MCP_TOOLSET_PG_TABLE"

#: Default Postgres table name.
DEFAULT_PG_TABLE = "knowledge_documents"

#: Language used by Postgres full-text parsing for keyword retrieval.
DEFAULT_PG_LANGUAGE = "english"


def transcripts_dir() -> Path:
    """Return the directory where transcript markdown files are written.

    Reads ``MCP_TOOLSET_TRANSCRIPTS_DIR`` and falls back to ``./data/transcripts``.
    The directory is created if it does not yet exist.
    """
    path = Path(os.getenv(TRANSCRIPTS_DIR_ENV, DEFAULT_TRANSCRIPTS_DIR)).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def store_backend() -> str:
    """Return the configured store backend: ``"memory"`` (default) or ``"pgvector"``."""
    return os.getenv(STORE_BACKEND_ENV, "memory").strip().lower()


def pg_table() -> str:
    """Return the Postgres table name for the pgvector backend."""
    return os.getenv(PG_TABLE_ENV, DEFAULT_PG_TABLE)
