"""Export analysis as JSON file."""

import asyncio
import json

from sec_filing_agent import Agent


async def main() -> None:
    agent = Agent()
    report = await agent.analyze("AAPL", filing_type="10-K")

    with open("aapl_analysis.json", "w") as f:
        json.dump(report.model_dump(), f, indent=2, default=str)

    print(f"Saved to aapl_analysis.json")
    print(f"Company: {report.company_name}")
    print(f"Cost: ${report.model_usage.estimated_cost_usd:.3f}")


if __name__ == "__main__":
    asyncio.run(main())
