I built an open-source AI tool that analyzes SEC filings

After building financial AI systems, I open-sourced a tool that fetches SEC filings (10-K, 10-Q, 8-K) and generates structured analysis reports.

What makes it different:
- Financial numbers from XBRL structured data (never hallucinated)
- AI only used for qualitative analysis where it adds value
- Model routing optimizes cost (~$0.02/report)
- Structured JSON output, not free-text

pip install sec-filing-agent
sec-agent analyze AAPL

Built with Python, Claude API, and edgartools.

GitHub: https://github.com/Dabaiee/sec-filing-agent

#AI #FinTech #OpenSource #Python #LLM
