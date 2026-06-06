"""Offline smoke-test pipeline: a single text-statistics component."""

from __future__ import annotations

from haystack import Pipeline

from mcp_toolset.custom_components import TextStatistics


def build_text_stats_pipeline() -> Pipeline:
    """Build a one-component pipeline that computes text statistics."""
    pipeline = Pipeline()
    pipeline.add_component("stats", TextStatistics())
    return pipeline
