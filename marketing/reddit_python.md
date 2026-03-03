# I built an open-source CLI tool that analyzes SEC filings with AI

`pip install sec-filing-agent`

One command: `sec-agent analyze AAPL` -> structured report with risk factors, financial highlights, and event summaries.

Key technical decisions:
- edgartools for SEC data fetching (no wheel reinvention)
- XBRL for financial numbers (no LLM hallucination on numbers)
- Model routing: Sonnet for reasoning, Haiku for extraction (~5x cost reduction)
- Pydantic for all LLM output validation with auto-retry
- Rich terminal UI showing which model handles each pipeline stage
- TTL cache for SEC API calls during batch operations

GitHub: https://github.com/Dabaiee/sec-filing-agent
PyPI: https://pypi.org/project/sec-filing-agent/

Would love feedback on the architecture. PRs welcome.
