"""Batch analysis example — analyze multiple tickers."""

import asyncio
import json

from sec_filing_agent import analyze


async def main() -> None:
    tickers = ["AAPL", "MSFT", "GOOGL"]

    for ticker in tickers:
        print(f"\n{'='*60}")
        print(f"Analyzing {ticker}...")
        print(f"{'='*60}")

        try:
            report = await analyze(ticker, output_format="json")
            print(f"  Company: {report.company_name}")
            print(f"  Filing: {report.filing_type} ({report.filing_date})")
            print(f"  Summary: {report.summary[:100]}...")
            print(f"  Cost: ${report.model_usage.estimated_cost_usd:.3f}")
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
