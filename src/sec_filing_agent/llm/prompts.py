"""Prompt templates for all LLM-powered pipeline stages."""

from __future__ import annotations

CLASSIFY_FILING_PROMPT = """\
You are a SEC filing classification expert. Given the beginning of an SEC filing document, \
identify the filing type and extract metadata.

Filing content (first 3000 chars):
{content}

Respond with a JSON object:
{{
  "filing_type": "10-K" | "10-Q" | "8-K",
  "company_name": "<company name>",
  "period_of_report": "<period covered, e.g. December 31, 2024>"
}}
"""

TEN_K_ANALYSIS_PROMPT = """\
You are a senior financial analyst. Analyze this 10-K annual report filing and produce a \
structured analysis report.

Company: {company_name} ({ticker})
Filing Date: {filing_date}
Period of Report: {period_of_report}

Filing content:
{content}

Provide your analysis as a JSON object with these fields:
{{
  "summary": "<2-3 sentence executive summary of the annual report>",
  "management_discussion": "<key points from MD&A section>",
  "forward_looking": ["<forward-looking statement 1>", "<statement 2>", ...]
}}
"""

TEN_K_RISK_FACTORS_PROMPT = """\
You are a risk analysis expert. Extract the top 5 risk factors from this 10-K filing.

Company: {company_name} ({ticker})

Filing content:
{content}

Provide your analysis as a JSON object:
{{
  "risk_factors": [
    {{
      "category": "regulatory" | "market" | "operational" | "financial" | "competitive",
      "title": "<short risk title>",
      "description": "<detailed description>",
      "severity": "high" | "medium" | "low"
    }}
  ]
}}
"""

TEN_K_FINANCIALS_PROMPT = """\
You are a financial data extraction expert. Extract key financial highlights from this 10-K filing.

Company: {company_name} ({ticker})

Filing content:
{content}

Provide your analysis as a JSON object:
{{
  "revenue": "<total revenue, e.g. $394.3B>",
  "net_income": "<net income, e.g. $93.7B>",
  "gross_margin": "<gross margin %, e.g. 46.2%>",
  "operating_margin": "<operating margin %, e.g. 30.1%>",
  "yoy_revenue_change": "<YoY change, e.g. +2.0%>",
  "key_metrics": {{"<metric name>": "<value>", ...}}
}}
"""

TEN_Q_ANALYSIS_PROMPT = """\
You are a senior financial analyst. Analyze this 10-Q quarterly report filing and produce a \
structured analysis.

Company: {company_name} ({ticker})
Filing Date: {filing_date}
Period of Report: {period_of_report}

Filing content:
{content}

Provide your analysis as a JSON object:
{{
  "summary": "<2-3 sentence executive summary of the quarterly report>",
  "management_discussion": "<key highlights from management commentary>",
  "forward_looking": ["<forward-looking statement 1>", "<statement 2>", ...]
}}
"""

TEN_Q_FINANCIALS_PROMPT = """\
You are a financial data extraction expert. Extract quarterly financial highlights from this 10-Q.

Company: {company_name} ({ticker})

Filing content:
{content}

Provide your analysis as a JSON object:
{{
  "revenue": "<quarterly revenue>",
  "net_income": "<quarterly net income>",
  "gross_margin": "<gross margin %>",
  "operating_margin": "<operating margin %>",
  "yoy_revenue_change": "<YoY quarterly change>",
  "key_metrics": {{"<metric>": "<value>", ...}}
}}
"""

EIGHT_K_ANALYSIS_PROMPT = """\
You are a corporate events analyst. Analyze this 8-K current report filing.

Company: {company_name} ({ticker})
Filing Date: {filing_date}

Filing content:
{content}

Provide your analysis as a JSON object:
{{
  "summary": "<2-3 sentence summary of the event(s) reported>",
  "key_events": [
    {{
      "event_type": "earnings" | "acquisition" | "leadership" | "restructuring" | "other",
      "headline": "<event headline>",
      "details": "<event details>",
      "material_impact": "high" | "medium" | "low"
    }}
  ]
}}
"""

EIGHT_K_FINANCIALS_PROMPT = """\
You are a financial data extraction expert. Extract any financial figures from this 8-K filing.

Company: {company_name} ({ticker})

Filing content:
{content}

Provide your analysis as a JSON object:
{{
  "revenue": "<revenue if mentioned, else null>",
  "net_income": "<net income if mentioned, else null>",
  "gross_margin": "<if mentioned, else null>",
  "operating_margin": "<if mentioned, else null>",
  "yoy_revenue_change": "<if mentioned, else null>",
  "key_metrics": {{"<metric>": "<value>", ...}}
}}
"""
