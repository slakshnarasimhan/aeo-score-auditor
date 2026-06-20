"""Shared report formatting helpers (mirrors frontend report-utils)."""

CATEGORY_DESCRIPTIONS = {
    "answerability": "How well the content directly answers questions",
    "structured_data": "Implementation of Schema.org and structured markup",
    "authority": "Author credentials, citations, and trust signals",
    "content_quality": "Depth, uniqueness, and freshness of content",
    "citationability": "Clarity of facts, data tables, and trustworthiness",
    "technical": "Page performance, mobile-friendliness, and SEO basics",
    "ai_citation": "Likelihood of being cited by AI models",
}

CATEGORY_ACTIONS = {
    "answerability": "Add direct Q&A sections, FAQ blocks, and concise answers at the top of key pages.",
    "structured_data": "Implement Schema.org markup (FAQ, Article, Organization) and validate with Google Rich Results.",
    "authority": "Add author bios, citations, credentials, and external references to build trust signals.",
    "content_quality": "Expand thin content, update stale pages, and add unique insights competitors lack.",
    "citationability": "Include clear facts, statistics, tables, and quotable statements AI can reference.",
    "technical": "Improve page speed, mobile responsiveness, meta tags, and crawlability.",
    "ai_citation": "Structure content for AI extraction: clear headings, definitions, and factual statements.",
}


def format_category_name(category: str) -> str:
    return category.replace("_", " ").title()


def get_category_description(category: str) -> str:
    return CATEGORY_DESCRIPTIONS.get(category, "")


def get_score_label(score: float) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 80:
        return "Strong"
    if score >= 70:
        return "Good"
    if score >= 60:
        return "Fair"
    if score >= 40:
        return "Needs Work"
    return "Critical"


def score_color_hex(percentage: float) -> str:
    if percentage >= 80:
        return "#10b981"
    if percentage >= 60:
        return "#f59e0b"
    if percentage >= 40:
        return "#f97316"
    return "#f43f5e"


def grade_color_hex(grade: str) -> str:
    if grade.startswith("A"):
        return "#10b981"
    if grade.startswith("B"):
        return "#f59e0b"
    if grade.startswith("C"):
        return "#f97316"
    return "#f43f5e"
