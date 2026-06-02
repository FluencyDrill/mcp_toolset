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


def transcripts_dir() -> Path:
    """Return the directory where transcript markdown files are written.

    Reads ``MCP_TOOLSET_TRANSCRIPTS_DIR`` and falls back to ``./data/transcripts``.
    The directory is created if it does not yet exist.
    """
    path = Path(os.getenv(TRANSCRIPTS_DIR_ENV, DEFAULT_TRANSCRIPTS_DIR)).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path
