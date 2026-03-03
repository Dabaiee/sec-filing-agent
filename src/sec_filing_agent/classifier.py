"""Filing type classification using heuristics — no LLM call needed.

Architecture decision: classification uses regex heuristics, NOT the LLM.
Filing types are deterministic metadata from EDGAR, so wasting an LLM call
for classification would be wasteful. The heuristic validates EDGAR's
reported type against the document content as a safety check.
"""

from __future__ import annotations

import re

from sec_filing_agent.models.filing import FilingMetadata, RawFiling


def classify_filing(raw: RawFiling) -> FilingMetadata:
    """Classify a filing and extract metadata.

    Uses regex/heuristic classification first. The filing type is typically
    already known from the EDGAR API, so this mainly validates and extracts
    the period of report.

    Args:
        raw: The raw filing data from EDGAR.

    Returns:
        FilingMetadata with classified type and extracted metadata.
    """
    filing_type = _detect_filing_type(raw)
    period_of_report = _extract_period_of_report(raw)

    return FilingMetadata(
        filing_type=filing_type,
        company_name=raw.company_name,
        ticker=raw.ticker,
        cik=raw.cik,
        filing_date=raw.filing_date,
        period_of_report=period_of_report,
    )


def _detect_filing_type(raw: RawFiling) -> str:
    """Detect the filing type from the raw filing.

    The filing type from EDGAR is usually reliable. We validate it against
    the document content as a sanity check.
    """
    known_type = raw.filing_type.upper().strip()
    if known_type in ("10-K", "10-Q", "8-K"):
        return known_type

    # Fallback: try to detect from content
    content_upper = raw.content[:5000].upper()

    if re.search(r"FORM\s+10-K\b", content_upper):
        return "10-K"
    if re.search(r"FORM\s+10-Q\b", content_upper):
        return "10-Q"
    if re.search(r"FORM\s+8-K\b", content_upper):
        return "8-K"

    # If we still can't determine, check for annual/quarterly keywords
    if "ANNUAL REPORT" in content_upper:
        return "10-K"
    if "QUARTERLY REPORT" in content_upper:
        return "10-Q"
    if "CURRENT REPORT" in content_upper:
        return "8-K"

    # Default to what EDGAR said
    return known_type


def _extract_period_of_report(raw: RawFiling) -> str:
    """Extract the period of report from filing content."""
    content = raw.content[:10000]

    # Look for "PERIOD OF REPORT" or "FOR THE FISCAL YEAR ENDED" patterns
    patterns = [
        r"(?:PERIOD\s+OF\s+REPORT|CONFORMED\s+PERIOD\s+OF\s+REPORT)\s*[:=]?\s*(\d{4}-\d{2}-\d{2}|\d{8})",
        r"(?:FOR\s+THE\s+(?:FISCAL\s+)?(?:YEAR|QUARTER|TRANSITION\s+PERIOD)\s+ENDED)\s+(\w+\s+\d{1,2},?\s+\d{4})",
        r"(?:PERIOD\s+OF\s+REPORT)\s*(\d{4}\d{2}\d{2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Fallback: use filing date
    return str(raw.filing_date)
