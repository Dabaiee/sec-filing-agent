"""Prompt templates for diff and comparison analysis."""

from __future__ import annotations

DIFF_PROMPT = """\
You are a senior financial analyst specializing in SEC filing analysis. Compare these two \
{filing_type} filings from {company_name} ({ticker}) filed at different times.

=== EARLIER FILING (Filed: {from_date}) ===
{from_content}

=== LATER FILING (Filed: {to_date}) ===
{to_content}

Analyze the key changes between these two filings. Respond with a JSON object:
{{
  "summary": "<2-3 sentence overview of the most significant changes>",
  "risk_changes": [
    {{
      "change_type": "added" | "removed" | "changed",
      "title": "<risk factor title>",
      "description": "<what changed>",
      "old_severity": "high" | "medium" | "low" | null,
      "new_severity": "high" | "medium" | "low" | null
    }}
  ],
  "financial_changes": [
    {{
      "metric": "<metric name, e.g. Revenue>",
      "old_value": "<value in earlier filing>",
      "new_value": "<value in later filing>",
      "change": "<change description, e.g. +2.5%>"
    }}
  ],
  "notable_changes": ["<other significant change 1>", "<change 2>", ...]
}}

Focus on the most material changes. Limit risk_changes to top 5-7 and financial_changes to key metrics.
"""

COMPARE_PROMPT = """\
You are a senior financial analyst. Compare the {filing_type} filings of these two companies.

=== {company_a} ({ticker_a}) — Filed: {date_a} ===
{content_a}

=== {company_b} ({ticker_b}) — Filed: {date_b} ===
{content_b}

Provide a comparative analysis as a JSON object:
{{
  "summary": "<2-3 sentence comparative overview>",
  "risk_comparison": [
    "<key difference in risk profiles 1>",
    "<key difference 2>",
    ...
  ],
  "financial_comparison": [
    {{
      "metric": "<metric name>",
      "old_value": "<{ticker_a} value>",
      "new_value": "<{ticker_b} value>",
      "change": "<comparison note>"
    }}
  ],
  "strengths_a": ["<{ticker_a} strength 1>", ...],
  "strengths_b": ["<{ticker_b} strength 1>", ...]
}}

Focus on material differences that would matter to an investor.
"""
