"""Shared fixtures for SEC Filing Agent tests."""

from __future__ import annotations

from datetime import date

import pytest

from sec_filing_agent.models.analysis import (
    AnalysisReport,
    FinancialHighlights,
    ModelUsage,
    RiskFactor,
    StageUsage,
)
from sec_filing_agent.models.filing import FilingMetadata, RawFiling


@pytest.fixture
def sample_10k_filing() -> RawFiling:
    """Sample 10-K filing for testing."""
    return RawFiling(
        ticker="AAPL",
        cik="0000320193",
        company_name="Apple Inc.",
        accession_number="0000320193-24-000123",
        filing_type="10-K",
        filing_date=date(2024, 11, 1),
        document_url="https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm",
        content=SAMPLE_10K_CONTENT,
    )


@pytest.fixture
def sample_10q_filing() -> RawFiling:
    """Sample 10-Q filing for testing."""
    return RawFiling(
        ticker="AAPL",
        cik="0000320193",
        company_name="Apple Inc.",
        accession_number="0000320193-24-000456",
        filing_type="10-Q",
        filing_date=date(2024, 8, 2),
        document_url="https://www.sec.gov/Archives/edgar/data/320193/000032019324000456/aapl-20240629.htm",
        content=SAMPLE_10Q_CONTENT,
    )


@pytest.fixture
def sample_8k_filing() -> RawFiling:
    """Sample 8-K filing for testing."""
    return RawFiling(
        ticker="AAPL",
        cik="0000320193",
        company_name="Apple Inc.",
        accession_number="0000320193-24-000789",
        filing_type="8-K",
        filing_date=date(2024, 10, 31),
        document_url="https://www.sec.gov/Archives/edgar/data/320193/000032019324000789/aapl-20241031.htm",
        content=SAMPLE_8K_CONTENT,
    )


@pytest.fixture
def sample_metadata() -> FilingMetadata:
    """Sample filing metadata."""
    return FilingMetadata(
        filing_type="10-K",
        company_name="Apple Inc.",
        ticker="AAPL",
        cik="0000320193",
        filing_date=date(2024, 11, 1),
        period_of_report="September 28, 2024",
    )


@pytest.fixture
def sample_report() -> AnalysisReport:
    """Sample analysis report for output formatting tests."""
    return AnalysisReport(
        ticker="AAPL",
        company_name="Apple Inc.",
        filing_type="10-K",
        filing_date=date(2024, 11, 1),
        period_of_report="September 28, 2024",
        summary="Apple reported $394.3B in revenue for fiscal 2024, up 2% YoY. Net income was $93.7B.",
        risk_factors=[
            RiskFactor(
                category="market",
                title="Global supply chain disruption",
                description="Dependence on global supply chains poses risks.",
                severity="high",
            ),
            RiskFactor(
                category="regulatory",
                title="EU regulatory scrutiny",
                description="Increasing antitrust actions in the European Union.",
                severity="medium",
            ),
        ],
        financial_highlights=FinancialHighlights(
            revenue="$394.3B",
            net_income="$93.7B",
            gross_margin="46.2%",
            operating_margin="30.1%",
            yoy_revenue_change="+2.0%",
        ),
        management_discussion="Apple continues to invest heavily in AI and services.",
        forward_looking=["Expect continued growth in Services segment."],
        model_usage=ModelUsage(
            stages=[
                StageUsage(stage="Analysis", model="claude-sonnet-4-20250514", input_tokens=2000, output_tokens=500),
                StageUsage(stage="Extraction", model="claude-haiku-4-5-20251001", input_tokens=1500, output_tokens=300),
            ],
            total_input_tokens=3500,
            total_output_tokens=800,
            estimated_cost_usd=0.024,
        ),
        pipeline_duration_ms=5200,
    )


# --- Sample filing content snippets ---

SAMPLE_10K_CONTENT = """FORM 10-K
ANNUAL REPORT PURSUANT TO SECTION 13 OR 15(d) OF THE SECURITIES EXCHANGE ACT OF 1934

For the fiscal year ended September 28, 2024

Commission File Number: 001-36743

APPLE INC.
One Apple Park Way
Cupertino, California 95014

ITEM 1. BUSINESS
Apple Inc. designs, manufactures and markets smartphones, personal computers, tablets, wearables and accessories,
and sells a variety of related services. The Company's fiscal year is the 52- or 53-week period that ends on the
last Saturday of September.

Products: iPhone, Mac, iPad, Wearables/Home/Accessories
Services: Advertising, AppleCare, Cloud Services, Digital Content, Payment Services

ITEM 1A. RISK FACTORS
Global supply chain dependencies could disrupt product availability.
Regulatory changes in the EU may impact App Store revenue models.
Intense competition in AI and machine learning from major tech companies.
Foreign currency fluctuations affect international revenue.
Cybersecurity threats pose operational risks.

ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS
Total net revenue was $394.3 billion, an increase of 2% year over year.
Net income was $93.7 billion. Gross margin was 46.2%.
Services revenue grew 14% to reach $96.2 billion.
The company returned over $100 billion to shareholders through dividends and buybacks.

PERIOD OF REPORT: September 28, 2024
"""

SAMPLE_10Q_CONTENT = """FORM 10-Q
QUARTERLY REPORT PURSUANT TO SECTION 13 OR 15(d) OF THE SECURITIES EXCHANGE ACT OF 1934

For the quarterly period ended June 29, 2024

APPLE INC.

ITEM 2. MANAGEMENT'S DISCUSSION AND ANALYSIS
Revenue for Q3 FY2024 was $85.8 billion, up 5% year over year.
iPhone revenue was $39.3 billion. Services reached $24.2 billion.
Gross margin improved to 46.3%.
"""

SAMPLE_8K_CONTENT = """FORM 8-K
CURRENT REPORT
Pursuant to Section 13 or 15(d) of the Securities Exchange Act of 1934

Date of Report: October 31, 2024

APPLE INC.

Item 2.02 Results of Operations and Financial Condition

Apple today announced financial results for its fiscal 2024 fourth quarter ended September 28, 2024.
The Company posted quarterly revenue of $94.9 billion, up 6 percent year over year, and quarterly
earnings per diluted share of $1.64.

"Today Apple is reporting a new September quarter revenue record of $94.9 billion, up 6 percent
from a year ago," said Tim Cook, Apple's CEO.
"""
