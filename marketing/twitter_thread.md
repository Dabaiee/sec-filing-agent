Tweet 1:
I built an open-source tool that reads SEC filings so you don't have to.

sec-agent analyze AAPL -> structured risk factors, financials, key events

The trick: financial numbers come from XBRL (never hallucinated). AI only does qualitative analysis.

Thread:

Tweet 2:
The pipeline:
1. Fetch filing from SEC EDGAR
2. Classify filing type (10-K, 10-Q, 8-K)
3. Route to specialized analyzer
4. Extract data (XBRL for numbers, LLM for risk/sentiment)
5. Validate output with Pydantic
6. Format as JSON/terminal/markdown

Tweet 3:
Model routing saves ~80% on API costs:
- Complex reasoning (risk analysis) -> Sonnet
- Simple extraction (entities, classification) -> Haiku
- Financial numbers -> XBRL (free, no LLM)

Each pipeline stage shows which model is running.

Tweet 4:
pip install sec-filing-agent
sec-agent analyze AAPL

Open source, MIT license.
GitHub: https://github.com/Dabaiee/sec-filing-agent
