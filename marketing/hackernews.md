# Show HN: SEC Filing Intelligence Agent – AI analysis of 10-K/10-Q/8-K filings

Link: https://github.com/Dabaiee/sec-filing-agent

I built an open-source CLI tool that fetches SEC filings and generates structured analysis reports using LLM pipelines.

What makes it different from pasting filings into ChatGPT:

- Financial numbers come from XBRL data (never hallucinated)
- LLM is only used for qualitative analysis (risk factors, MD&A)
- Model routing: Sonnet for complex analysis, Haiku for classification (~$0.02/report vs $0.10+)
- Structured JSON output with Pydantic validation
- pip install sec-filing-agent && sec-agent analyze AAPL

Built with Python, Anthropic Claude API, and edgartools for SEC data.

Happy to answer questions about the hybrid XBRL+LLM architecture or model routing approach.
