"""
Business-aware audit profiles.

These profiles describe what AI/search systems should be able to extract
from different kinds of websites. They complement page-level content types.
"""
from typing import Dict, List


AUTO_PROFILE = "auto"
ECOMMERCE_PROFILE = "ecommerce"
SAAS_APP_PROFILE = "saas_app"
PUBLISHER_PROFILE = "publisher"
LOCAL_BUSINESS_PROFILE = "local_business"
EDUCATION_PROFILE = "education"
DOCUMENTATION_PROFILE = "documentation"
DEFAULT_PROFILE = "general"


class AuditProfile:
    """Profile describing extraction goals and category applicability."""

    def __init__(
        self,
        key: str,
        label: str,
        description: str,
        extraction_goals: List[str],
        category_applicability: Dict[str, Dict[str, str]],
        recommended_schema: List[str],
        not_applicable: List[str] = None,
    ):
        self.key = key
        self.label = label
        self.description = description
        self.extraction_goals = extraction_goals
        self.category_applicability = category_applicability
        self.recommended_schema = recommended_schema
        self.not_applicable = not_applicable or []

    def applicability_for(self, category: str) -> Dict[str, str]:
        return self.category_applicability.get(
            category,
            {
                "level": "medium",
                "reason": "This signal can help AI systems understand and reuse the page.",
            },
        )

    def to_dict(self, confidence: str = "medium", reason: str = "") -> Dict:
        return {
            "type": self.key,
            "label": self.label,
            "confidence": confidence,
            "description": self.description,
            "reason": reason,
            "extraction_goals": self.extraction_goals,
            "recommended_schema": self.recommended_schema,
            "not_applicable": self.not_applicable,
        }


BASE_APPLICABILITY = {
    "answerability": {
        "level": "medium",
        "reason": "Concise answers help AI systems summarize the page, but not every page needs a full FAQ posture.",
    },
    "structured_data": {
        "level": "high",
        "reason": "Schema markup is a direct machine-readable extraction path.",
    },
    "authority": {
        "level": "medium",
        "reason": "Trust signals help AI systems decide whether extracted information is reliable.",
    },
    "content_quality": {
        "level": "high",
        "reason": "Clear, specific content improves extraction accuracy.",
    },
    "citationability": {
        "level": "medium",
        "reason": "Facts and quotable statements are useful when the page is meant to be cited.",
    },
    "technical": {
        "level": "high",
        "reason": "Pages must be crawlable and readable before their information can be extracted.",
    },
    "ai_citation": {
        "level": "medium",
        "reason": "Direct AI citation checks are useful when enabled, but this audit can still provide deterministic guidance without them.",
    },
}


PROFILES = {
    DEFAULT_PROFILE: AuditProfile(
        key=DEFAULT_PROFILE,
        label="General Website",
        description="Balanced extraction readiness for mixed-purpose websites.",
        extraction_goals=[
            "entity_identity",
            "primary_topic",
            "main_offering",
            "audience_fit",
            "trust_signals",
            "next_step",
        ],
        category_applicability=BASE_APPLICABILITY,
        recommended_schema=["Organization", "WebSite", "BreadcrumbList"],
    ),
    ECOMMERCE_PROFILE: AuditProfile(
        key=ECOMMERCE_PROFILE,
        label="Ecommerce",
        description="Optimized for product, offer, review, availability, and buying-context extraction.",
        extraction_goals=[
            "product_name",
            "price",
            "availability",
            "product_specs",
            "variants",
            "reviews",
            "shipping_returns",
            "comparison_context",
        ],
        category_applicability={
            **BASE_APPLICABILITY,
            "answerability": {
                "level": "medium",
                "reason": "FAQ content helps objections, sizing, shipping, and returns, but product facts matter more than article-style answers.",
            },
            "structured_data": {
                "level": "critical",
                "reason": "Product, Offer, AggregateRating, and Breadcrumb schema are core extraction signals for ecommerce.",
            },
            "citationability": {
                "level": "low",
                "reason": "The page is primarily commercial, so citeable research density is less important than product facts.",
            },
            "technical": {
                "level": "critical",
                "reason": "Commerce pages need fast, crawlable rendering so inventory, price, and offer details are visible.",
            },
        },
        recommended_schema=["Product", "Offer", "AggregateRating", "Review", "BreadcrumbList"],
        not_applicable=["article_author_byline", "long_form_citation_density"],
    ),
    SAAS_APP_PROFILE: AuditProfile(
        key=SAAS_APP_PROFILE,
        label="SaaS / App",
        description="Optimized for app identity, capability, audience, platform, pricing, and proof extraction.",
        extraction_goals=[
            "app_name",
            "core_use_case",
            "target_audience",
            "key_features",
            "supported_platforms",
            "pricing_or_trial",
            "proof_points",
            "privacy_support",
        ],
        category_applicability={
            **BASE_APPLICABILITY,
            "answerability": {
                "level": "medium",
                "reason": "Focused FAQs help users and AI systems understand fit, pricing, privacy, and setup.",
            },
            "structured_data": {
                "level": "high",
                "reason": "SoftwareApplication, Product, FAQ, and Organization schema can expose the app clearly.",
            },
            "authority": {
                "level": "high",
                "reason": "Testimonials, product proof, company identity, and policies matter more than article bylines.",
            },
            "citationability": {
                "level": "low",
                "reason": "This page does not need dense external citations unless it makes factual learning claims.",
            },
        },
        recommended_schema=["SoftwareApplication", "Organization", "FAQPage", "Product"],
        not_applicable=["shipping_policy", "inventory_availability", "article_author_byline"],
    ),
    PUBLISHER_PROFILE: AuditProfile(
        key=PUBLISHER_PROFILE,
        label="Publisher / Blog",
        description="Optimized for answer extraction, citations, authorship, freshness, and topic authority.",
        extraction_goals=[
            "direct_answer",
            "topic_coverage",
            "author_expertise",
            "publication_date",
            "source_citations",
            "definitions",
            "key_takeaways",
        ],
        category_applicability={
            **BASE_APPLICABILITY,
            "answerability": {
                "level": "critical",
                "reason": "Informational content should directly answer likely questions.",
            },
            "authority": {
                "level": "critical",
                "reason": "Authors, dates, and sources are central trust signals for publishable answers.",
            },
            "citationability": {
                "level": "critical",
                "reason": "Facts, statistics, tables, and references make the content easier to cite.",
            },
        },
        recommended_schema=["Article", "BlogPosting", "FAQPage", "Person", "Organization"],
    ),
    LOCAL_BUSINESS_PROFILE: AuditProfile(
        key=LOCAL_BUSINESS_PROFILE,
        label="Local Business",
        description="Optimized for business identity, location, services, opening hours, reviews, and contact extraction.",
        extraction_goals=[
            "business_name",
            "address",
            "service_area",
            "opening_hours",
            "phone",
            "services",
            "reviews",
            "booking_or_contact",
        ],
        category_applicability={
            **BASE_APPLICABILITY,
            "structured_data": {
                "level": "critical",
                "reason": "LocalBusiness, Service, PostalAddress, and opening-hour markup are direct local extraction signals.",
            },
            "citationability": {
                "level": "low",
                "reason": "The page needs clear business facts more than research-style citations.",
            },
        },
        recommended_schema=["LocalBusiness", "Service", "PostalAddress", "AggregateRating", "FAQPage"],
        not_applicable=["article_author_byline", "research_citations"],
    ),
    EDUCATION_PROFILE: AuditProfile(
        key=EDUCATION_PROFILE,
        label="Education / Course",
        description="Optimized for learning outcome, audience, curriculum, instructor, pricing, and enrollment extraction.",
        extraction_goals=[
            "course_or_program_name",
            "learning_outcomes",
            "target_level",
            "curriculum",
            "instructor_or_provider",
            "duration",
            "price",
            "enrollment_path",
        ],
        category_applicability={
            **BASE_APPLICABILITY,
            "structured_data": {
                "level": "high",
                "reason": "Course, Organization, FAQ, and Review schema help expose the learning offer.",
            },
            "authority": {
                "level": "high",
                "reason": "Instructor/provider credibility matters for education-related extraction.",
            },
        },
        recommended_schema=["Course", "EducationalOrganization", "FAQPage", "Review"],
    ),
    DOCUMENTATION_PROFILE: AuditProfile(
        key=DOCUMENTATION_PROFILE,
        label="Documentation",
        description="Optimized for task, API, troubleshooting, code, and version-aware extraction.",
        extraction_goals=[
            "task_or_api_name",
            "prerequisites",
            "steps",
            "parameters",
            "examples",
            "errors",
            "version",
            "related_docs",
        ],
        category_applicability={
            **BASE_APPLICABILITY,
            "answerability": {
                "level": "critical",
                "reason": "Documentation should answer task and troubleshooting questions directly.",
            },
            "technical": {
                "level": "critical",
                "reason": "Docs must be crawlable, linkable, and structured for repeated extraction.",
            },
            "citationability": {
                "level": "medium",
                "reason": "Examples and exact parameter facts matter more than external citations.",
            },
        },
        recommended_schema=["TechArticle", "HowTo", "FAQPage", "BreadcrumbList"],
    ),
}


KEYWORD_HINTS = {
    ECOMMERCE_PROFILE: [
        "add to cart",
        "checkout",
        "shipping",
        "returns",
        "sku",
        "in stock",
        "product",
        "variants",
    ],
    SAAS_APP_PROFILE: [
        "app",
        "software",
        "platform",
        "features",
        "free trial",
        "download",
        "ios",
        "android",
        "subscription",
        "dashboard",
    ],
    PUBLISHER_PROFILE: ["article", "blog", "guide", "news", "author", "published", "sources"],
    LOCAL_BUSINESS_PROFILE: [
        "address",
        "opening hours",
        "call us",
        "book appointment",
        "near me",
        "service area",
    ],
    EDUCATION_PROFILE: [
        "course",
        "curriculum",
        "lesson",
        "learn",
        "students",
        "instructor",
        "certificate",
    ],
    DOCUMENTATION_PROFILE: ["docs", "api", "sdk", "install", "configure", "reference", "endpoint"],
}


SCHEMA_HINTS = {
    "Product": ECOMMERCE_PROFILE,
    "Offer": ECOMMERCE_PROFILE,
    "SoftwareApplication": SAAS_APP_PROFILE,
    "WebApplication": SAAS_APP_PROFILE,
    "MobileApplication": SAAS_APP_PROFILE,
    "Article": PUBLISHER_PROFILE,
    "BlogPosting": PUBLISHER_PROFILE,
    "NewsArticle": PUBLISHER_PROFILE,
    "LocalBusiness": LOCAL_BUSINESS_PROFILE,
    "Restaurant": LOCAL_BUSINESS_PROFILE,
    "Course": EDUCATION_PROFILE,
    "EducationalOrganization": EDUCATION_PROFILE,
    "TechArticle": DOCUMENTATION_PROFILE,
    "HowTo": DOCUMENTATION_PROFILE,
}


def get_audit_profile(profile_key: str) -> AuditProfile:
    """Return a known profile, falling back to the balanced general profile."""
    return PROFILES.get(profile_key, PROFILES[DEFAULT_PROFILE])


def normalize_profile_key(profile_key: str) -> str:
    if not profile_key:
        return AUTO_PROFILE
    normalized = profile_key.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "app": SAAS_APP_PROFILE,
        "saas": SAAS_APP_PROFILE,
        "software": SAAS_APP_PROFILE,
        "product_app": SAAS_APP_PROFILE,
        "blog": PUBLISHER_PROFILE,
        "publishing": PUBLISHER_PROFILE,
        "local": LOCAL_BUSINESS_PROFILE,
        "course": EDUCATION_PROFILE,
        "docs": DOCUMENTATION_PROFILE,
        "documentation": DOCUMENTATION_PROFILE,
        "commerce": ECOMMERCE_PROFILE,
        "e_commerce": ECOMMERCE_PROFILE,
    }
    return aliases.get(normalized, normalized)


def infer_audit_profile(page_data: Dict, requested_profile: str = AUTO_PROFILE) -> Dict:
    """
    Infer or honor the business profile for an audit.

    Returns a serializable profile dict with confidence and reasoning.
    """
    requested = normalize_profile_key(requested_profile)
    if requested != AUTO_PROFILE and requested in PROFILES:
        profile = get_audit_profile(requested)
        return profile.to_dict(
            confidence="manual",
            reason=f"Selected audit profile override: {profile.label}.",
        )

    text_parts = [
        page_data.get("title", ""),
        page_data.get("meta_description", ""),
        page_data.get("main_content", "")[:6000],
        page_data.get("url", ""),
    ]
    text = " ".join(text_parts).lower()

    scores = {key: 0 for key in PROFILES if key != DEFAULT_PROFILE}
    schema_types = page_data.get("schema_types") or []
    for schema_type in schema_types:
        if isinstance(schema_type, list):
            candidates = schema_type
        else:
            candidates = [schema_type]
        for candidate in candidates:
            profile_key = SCHEMA_HINTS.get(candidate)
            if profile_key:
                scores[profile_key] += 4

    content_type = (page_data.get("content_type") or {}).get("type")
    if content_type == "transactional":
        scores[ECOMMERCE_PROFILE] += 1
        scores[SAAS_APP_PROFILE] += 1
    elif content_type == "informational":
        scores[PUBLISHER_PROFILE] += 1
    elif content_type == "navigational":
        for key in scores:
            scores[key] = max(scores[key] - 1, 0)

    for profile_key, keywords in KEYWORD_HINTS.items():
        for keyword in keywords:
            if keyword in text:
                scores[profile_key] += 1

    best_key = max(scores, key=scores.get)
    best_score = scores[best_key]

    if best_score <= 1:
        profile = get_audit_profile(DEFAULT_PROFILE)
        return profile.to_dict(
            confidence="low",
            reason="No strong business-context signals were detected, so a balanced profile was used.",
        )

    confidence = "high" if best_score >= 5 else "medium"
    profile = get_audit_profile(best_key)
    return profile.to_dict(
        confidence=confidence,
        reason=f"Detected {profile.label.lower()} signals from schema, URL, and page language.",
    )
