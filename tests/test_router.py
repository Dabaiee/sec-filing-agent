"""Tests for filing router with registry pattern."""

from __future__ import annotations

import pytest

from sec_filing_agent.analyzers.eight_k import EightKAnalyzer
from sec_filing_agent.analyzers.ten_k import TenKAnalyzer
from sec_filing_agent.analyzers.ten_q import TenQAnalyzer
from sec_filing_agent.router import (
    RouterError,
    get_analyzer,
    list_supported_types,
    register_analyzer,
)


def test_route_10k():
    analyzer = get_analyzer("10-K")
    assert isinstance(analyzer, TenKAnalyzer)


def test_route_10q():
    analyzer = get_analyzer("10-Q")
    assert isinstance(analyzer, TenQAnalyzer)


def test_route_8k():
    analyzer = get_analyzer("8-K")
    assert isinstance(analyzer, EightKAnalyzer)


def test_route_case_insensitive():
    analyzer = get_analyzer("10-k")
    assert isinstance(analyzer, TenKAnalyzer)


def test_route_unknown_type():
    with pytest.raises(RouterError, match="No analyzer available"):
        get_analyzer("20-F")


def test_list_supported_types():
    """List returns all default types."""
    types = list_supported_types()
    assert "10-K" in types
    assert "10-Q" in types
    assert "8-K" in types


def test_register_custom_analyzer():
    """Custom analyzers can be registered at runtime."""
    # Register a custom analyzer (reuse TenKAnalyzer as a stand-in)
    register_analyzer("20-F", TenKAnalyzer)
    analyzer = get_analyzer("20-F")
    assert isinstance(analyzer, TenKAnalyzer)
    assert "20-F" in list_supported_types()
