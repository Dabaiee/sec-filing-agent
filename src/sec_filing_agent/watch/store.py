"""SQLite storage for watchlist and historical analyses."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path.home() / ".sec-agent" / "watchlist.db"


class WatchStore:
    """SQLite-backed storage for watchlist data and analysis history."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self) -> None:
        """Create tables if they don't exist."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS watchlist (
                ticker TEXT PRIMARY KEY,
                added_at TEXT NOT NULL,
                last_checked TEXT,
                last_filing_date TEXT,
                last_accession TEXT
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                filing_type TEXT NOT NULL,
                filing_date TEXT NOT NULL,
                accession_number TEXT NOT NULL UNIQUE,
                analyzed_at TEXT NOT NULL,
                report_json TEXT NOT NULL,
                FOREIGN KEY (ticker) REFERENCES watchlist(ticker)
            );

            CREATE INDEX IF NOT EXISTS idx_analyses_ticker ON analyses(ticker);
            CREATE INDEX IF NOT EXISTS idx_analyses_filing_date ON analyses(filing_date);
        """)
        self._conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    # --- Watchlist CRUD ---

    def add_ticker(self, ticker: str) -> bool:
        """Add a ticker to the watchlist. Returns True if newly added."""
        ticker = ticker.upper()
        try:
            self._conn.execute(
                "INSERT INTO watchlist (ticker, added_at) VALUES (?, ?)",
                (ticker, datetime.now(UTC).isoformat()),
            )
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_ticker(self, ticker: str) -> bool:
        """Remove a ticker from the watchlist. Returns True if it existed."""
        ticker = ticker.upper()
        cursor = self._conn.execute(
            "DELETE FROM watchlist WHERE ticker = ?", (ticker,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def list_tickers(self) -> list[dict[str, Any]]:
        """List all tickers in the watchlist with their metadata."""
        cursor = self._conn.execute(
            "SELECT ticker, added_at, last_checked, last_filing_date FROM watchlist ORDER BY ticker"
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_ticker_info(self, ticker: str) -> dict[str, Any] | None:
        """Get watchlist info for a single ticker."""
        cursor = self._conn.execute(
            "SELECT * FROM watchlist WHERE ticker = ?", (ticker.upper(),)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_last_checked(self, ticker: str, filing_date: str | None = None, accession: str | None = None) -> None:
        """Update the last checked timestamp and optionally the last filing info."""
        ticker = ticker.upper()
        now = datetime.now(UTC).isoformat()
        if filing_date and accession:
            self._conn.execute(
                "UPDATE watchlist SET last_checked = ?, last_filing_date = ?, last_accession = ? WHERE ticker = ?",
                (now, filing_date, accession, ticker),
            )
        else:
            self._conn.execute(
                "UPDATE watchlist SET last_checked = ? WHERE ticker = ?",
                (now, ticker),
            )
        self._conn.commit()

    # --- Analysis History ---

    def save_analysis(self, ticker: str, filing_type: str, filing_date: str, accession: str, report_json: str) -> None:
        """Save an analysis report to history."""
        try:
            self._conn.execute(
                "INSERT INTO analyses (ticker, filing_type, filing_date, accession_number, analyzed_at, report_json) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (ticker.upper(), filing_type, filing_date, accession, datetime.now(UTC).isoformat(), report_json),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            pass  # Already analyzed this filing

    def get_latest_analysis(self, ticker: str, filing_type: str | None = None) -> dict[str, Any] | None:
        """Get the most recent analysis for a ticker."""
        if filing_type:
            cursor = self._conn.execute(
                "SELECT * FROM analyses WHERE ticker = ? AND filing_type = ? ORDER BY filing_date DESC LIMIT 1",
                (ticker.upper(), filing_type),
            )
        else:
            cursor = self._conn.execute(
                "SELECT * FROM analyses WHERE ticker = ? ORDER BY filing_date DESC LIMIT 1",
                (ticker.upper(),),
            )
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result["report"] = json.loads(result["report_json"])
            return result
        return None

    def get_analyses(self, ticker: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent analyses for a ticker."""
        cursor = self._conn.execute(
            "SELECT * FROM analyses WHERE ticker = ? ORDER BY filing_date DESC LIMIT ?",
            (ticker.upper(), limit),
        )
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result["report"] = json.loads(result["report_json"])
            results.append(result)
        return results

    def has_been_analyzed(self, accession: str) -> bool:
        """Check if a filing has already been analyzed."""
        cursor = self._conn.execute(
            "SELECT 1 FROM analyses WHERE accession_number = ?", (accession,)
        )
        return cursor.fetchone() is not None
