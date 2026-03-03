"""Webhook notification support for watchlist alerts."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


async def send_alert(
    webhook_url: str,
    ticker: str,
    filing_type: str,
    filing_date: str,
    summary: str,
) -> bool:
    """Send a webhook alert for a new filing analysis.

    Supports Slack-style and Discord-style webhook payloads.

    Args:
        webhook_url: The webhook URL to POST to.
        ticker: Stock ticker symbol.
        filing_type: Filing type (10-K, 10-Q, 8-K).
        filing_date: Filing date string.
        summary: Analysis summary text.

    Returns:
        True if the alert was sent successfully.
    """
    # Build a payload that works with both Slack and Discord webhooks
    text = (
        f"*New SEC Filing Alert*\n"
        f"*{ticker}* — {filing_type} (Filed: {filing_date})\n\n"
        f"{summary}"
    )

    # Slack format
    payload = {
        "text": text,
        "content": text,  # Discord compatibility
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            logger.info("Alert sent for %s %s", ticker, filing_type)
            return True
    except Exception as e:
        logger.warning("Failed to send alert for %s: %s", ticker, e)
        return False
