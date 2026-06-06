"""Prompt template loading.

Templates are plain ``.jinja`` files living next to this module. Load one and hand the
string to a Haystack ``PromptBuilder``::

    from haystack.components.builders import PromptBuilder
    from mcp_toolset.prompt_templates import load_template

    builder = PromptBuilder(template=load_template("example"))

This folder is scaffolding for now — no default pipeline uses it yet. It's where the
documented "answer over transcript" LLM upgrade would live.
"""

from __future__ import annotations

from pathlib import Path

_TEMPLATE_DIR = Path(__file__).parent


def load_template(name: str) -> str:
    """Load a ``.jinja`` template by name (without extension) from this package."""
    path = _TEMPLATE_DIR / f"{name}.jinja"
    if not path.exists():
        available = sorted(p.stem for p in _TEMPLATE_DIR.glob("*.jinja"))
        raise FileNotFoundError(f"Prompt template {name!r} not found. Available: {available}")
    return path.read_text(encoding="utf-8")


__all__ = ["load_template"]
