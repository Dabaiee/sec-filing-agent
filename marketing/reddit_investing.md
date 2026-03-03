# Open-source tool that reads SEC filings (10-K, 10-Q, 8-K) and generates analysis reports

I built a free, open-source tool for analyzing SEC filings. Enter a ticker, get a structured report.

What it does:
- Fetches the latest filing from SEC EDGAR
- Extracts risk factors, financial highlights, key events
- Financial numbers come from XBRL (actual SEC data, not AI guessing)
- AI only used for summarization and risk analysis

Install: `pip install sec-filing-agent`
Run: `sec-agent analyze AAPL`

Free, open-source, MIT license. No account needed -- just an Anthropic API key (~$0.02 per analysis).

https://github.com/Dabaiee/sec-filing-agent
