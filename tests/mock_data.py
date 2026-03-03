"""Mock LLM response data for tests."""

MOCK_10K_ANALYSIS_JSON = """{
    "summary": "Apple reported $394.3B in revenue for fiscal 2024, up 2% YoY. Services grew 14% to $96.2B. Net income was $93.7B with 46.2% gross margin.",
    "management_discussion": "Apple continues to invest in AI/ML and services, returning over $100B to shareholders.",
    "forward_looking": ["Expect continued growth in Services segment", "Increasing investment in AI capabilities"]
}"""

MOCK_10K_RISKS_JSON = """{
    "risk_factors": [
        {"category": "market", "title": "Supply chain disruption", "description": "Global supply chain dependencies.", "severity": "high"},
        {"category": "regulatory", "title": "EU regulation", "description": "Antitrust scrutiny in EU.", "severity": "medium"},
        {"category": "competitive", "title": "AI competition", "description": "Competition in AI/ML.", "severity": "medium"},
        {"category": "financial", "title": "Currency risk", "description": "Foreign currency fluctuations.", "severity": "low"},
        {"category": "operational", "title": "Cybersecurity", "description": "Cybersecurity threats.", "severity": "medium"}
    ]
}"""

MOCK_10K_FINANCIALS_JSON = """{
    "revenue": "$394.3B",
    "net_income": "$93.7B",
    "gross_margin": "46.2%",
    "operating_margin": "30.1%",
    "yoy_revenue_change": "+2.0%",
    "key_metrics": {"Services Revenue": "$96.2B"}
}"""

MOCK_10Q_ANALYSIS_JSON = """{
    "summary": "Apple Q3 FY2024 revenue was $85.8B, up 5% YoY. iPhone revenue $39.3B, Services $24.2B.",
    "management_discussion": "Strong growth driven by iPhone and Services.",
    "forward_looking": ["Continued investment in AI features"]
}"""

MOCK_10Q_FINANCIALS_JSON = """{
    "revenue": "$85.8B",
    "net_income": null,
    "gross_margin": "46.3%",
    "operating_margin": null,
    "yoy_revenue_change": "+5.0%",
    "key_metrics": {"iPhone Revenue": "$39.3B"}
}"""

MOCK_8K_ANALYSIS_JSON = """{
    "summary": "Apple reported Q4 FY2024 quarterly revenue of $94.9B, up 6% YoY, with EPS of $1.64.",
    "key_events": [
        {"event_type": "earnings", "headline": "Record September quarter revenue", "details": "$94.9B revenue, up 6% YoY", "material_impact": "high"}
    ]
}"""

MOCK_8K_FINANCIALS_JSON = """{
    "revenue": "$94.9B",
    "net_income": null,
    "gross_margin": null,
    "operating_margin": null,
    "yoy_revenue_change": "+6.0%",
    "key_metrics": {"EPS": "$1.64"}
}"""
