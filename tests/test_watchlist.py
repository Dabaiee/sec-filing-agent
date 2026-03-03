"""Tests for watchlist store and CRUD operations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sec_filing_agent.watch.store import WatchStore


@pytest.fixture
def store(tmp_path: Path) -> WatchStore:
    """Create a WatchStore backed by a temporary SQLite database."""
    db_path = tmp_path / "test_watchlist.db"
    s = WatchStore(db_path=db_path)
    yield s
    s.close()


# ── Add / Remove ────────────────────────────────────────────────────────────


def test_add_ticker(store: WatchStore):
    """Adding a ticker returns True and is listed."""
    assert store.add_ticker("AAPL") is True
    tickers = store.list_tickers()
    assert len(tickers) == 1
    assert tickers[0]["ticker"] == "AAPL"


def test_add_duplicate_ticker(store: WatchStore):
    """Adding the same ticker twice returns False on second add."""
    store.add_ticker("AAPL")
    assert store.add_ticker("AAPL") is False


def test_add_normalizes_case(store: WatchStore):
    """Tickers are stored uppercase regardless of input case."""
    store.add_ticker("aapl")
    tickers = store.list_tickers()
    assert tickers[0]["ticker"] == "AAPL"


def test_remove_ticker(store: WatchStore):
    """Removing an existing ticker returns True and removes it."""
    store.add_ticker("MSFT")
    assert store.remove_ticker("MSFT") is True
    assert store.list_tickers() == []


def test_remove_missing_ticker(store: WatchStore):
    """Removing a non-existent ticker returns False."""
    assert store.remove_ticker("NOPE") is False


# ── List / Get ──────────────────────────────────────────────────────────────


def test_list_empty(store: WatchStore):
    """Empty watchlist returns empty list."""
    assert store.list_tickers() == []


def test_list_multiple(store: WatchStore):
    """Multiple tickers are returned in alphabetical order."""
    store.add_ticker("MSFT")
    store.add_ticker("AAPL")
    store.add_ticker("NVDA")
    tickers = [t["ticker"] for t in store.list_tickers()]
    assert tickers == ["AAPL", "MSFT", "NVDA"]


def test_get_ticker_info(store: WatchStore):
    """get_ticker_info returns metadata dict for existing ticker."""
    store.add_ticker("GOOG")
    info = store.get_ticker_info("GOOG")
    assert info is not None
    assert info["ticker"] == "GOOG"
    assert info["added_at"] is not None


def test_get_ticker_info_missing(store: WatchStore):
    """get_ticker_info returns None for non-existent ticker."""
    assert store.get_ticker_info("NOPE") is None


# ── Update / Check ──────────────────────────────────────────────────────────


def test_update_last_checked(store: WatchStore):
    """update_last_checked sets the last_checked timestamp."""
    store.add_ticker("AAPL")
    store.update_last_checked("AAPL")
    info = store.get_ticker_info("AAPL")
    assert info is not None
    assert info["last_checked"] is not None


def test_update_last_checked_with_filing(store: WatchStore):
    """update_last_checked with filing info updates all fields."""
    store.add_ticker("AAPL")
    store.update_last_checked("AAPL", filing_date="2024-01-15", accession="0001-24-000001")
    info = store.get_ticker_info("AAPL")
    assert info["last_filing_date"] == "2024-01-15"
    assert info["last_accession"] == "0001-24-000001"


# ── Analysis History ────────────────────────────────────────────────────────


def test_save_and_get_analysis(store: WatchStore):
    """Saved analysis can be retrieved."""
    store.add_ticker("TSLA")
    report = {"summary": "Tesla Q4 report"}
    store.save_analysis("TSLA", "10-K", "2024-01-15", "0001-24-000001", json.dumps(report))
    result = store.get_latest_analysis("TSLA")
    assert result is not None
    assert result["report"]["summary"] == "Tesla Q4 report"


def test_save_duplicate_accession(store: WatchStore):
    """Saving analysis with duplicate accession is silently ignored."""
    store.add_ticker("AAPL")
    report = json.dumps({"summary": "First"})
    store.save_analysis("AAPL", "10-K", "2024-01-15", "ACC-001", report)
    # Same accession number — should not raise
    store.save_analysis("AAPL", "10-K", "2024-01-15", "ACC-001", report)
    analyses = store.get_analyses("AAPL")
    assert len(analyses) == 1


def test_get_analyses_limit(store: WatchStore):
    """get_analyses respects the limit parameter."""
    store.add_ticker("AAPL")
    for i in range(5):
        store.save_analysis("AAPL", "10-K", f"2024-0{i+1}-15", f"ACC-{i:03d}", json.dumps({"i": i}))
    results = store.get_analyses("AAPL", limit=3)
    assert len(results) == 3


def test_has_been_analyzed(store: WatchStore):
    """has_been_analyzed returns True for known accession numbers."""
    store.add_ticker("AAPL")
    store.save_analysis("AAPL", "10-K", "2024-01-15", "ACC-XYZ", json.dumps({"x": 1}))
    assert store.has_been_analyzed("ACC-XYZ") is True
    assert store.has_been_analyzed("ACC-UNKNOWN") is False


def test_get_latest_analysis_by_type(store: WatchStore):
    """get_latest_analysis filters by filing type."""
    store.add_ticker("AAPL")
    store.save_analysis("AAPL", "10-K", "2024-01-15", "ACC-K", json.dumps({"type": "10-K"}))
    store.save_analysis("AAPL", "10-Q", "2024-04-15", "ACC-Q", json.dumps({"type": "10-Q"}))
    result = store.get_latest_analysis("AAPL", filing_type="10-Q")
    assert result is not None
    assert result["report"]["type"] == "10-Q"


def test_get_latest_analysis_missing(store: WatchStore):
    """get_latest_analysis returns None when no analysis exists."""
    assert store.get_latest_analysis("NOPE") is None
