"""
Content-Aware Scoring Profiles

Different content types have different priorities and scoring weights.
This module defines scoring profiles for each content type.
"""

# Content types (matching content_classifier.py)
INFORMATIONAL = "informational"
EXPERIENTIAL = "experiential"
TRANSACTIONAL = "transactional"
NAVIGATIONAL = "navigational"


class ScoringProfile:
    """Scoring profile for a content type"""
    
    def __init__(self, name: str, category_weights: dict, adjustments: dict = None):
        """
        Initialize scoring profile
        
        Args:
            name: Profile name
            category_weights: Weight multipliers for each category (0.0-2.0)
            adjustments: Optional dict of specific scoring adjustments
        """
        self.name = name
        self.category_weights = category_weights
        self.adjustments = adjustments or {}
    
    def get_weight(self, category: str) -> float:
        """Get weight multiplier for a category"""
        return self.category_weights.get(category, 1.0)
    
    def get_adjustment(self, key: str, default=None):
        """Get a specific adjustment"""
        return self.adjustments.get(key, default)


# Default profile (balanced scoring)
DEFAULT_PROFILE = ScoringProfile(
    name="default",
    category_weights={
        'answerability': 1.0,
        'structured_data': 1.0,
        'authority': 1.0,
        'content_quality': 1.0,
        'citationability': 1.0,
        'technical': 1.0
    }
)


# Informational content (articles, guides, tutorials, FAQs)
INFORMATIONAL_PROFILE = ScoringProfile(
    name="informational",
    category_weights={
        'answerability': 1.3,      # Higher weight - should answer questions
        'structured_data': 1.0,     # Standard
        'authority': 1.2,           # Higher weight - credibility is important
        'content_quality': 1.2,     # Higher weight - depth and freshness matter
        'citationability': 1.2,     # Higher weight - facts and data important
        'technical': 1.0            # Standard
    },
    adjustments={
        'require_questions': True,
        'require_answers': True,
        'min_word_count': 300,
        'prefer_h2_questions': True
    }
)


# Experiential content (experiences, stories, events, travel)
EXPERIENTIAL_PROFILE = ScoringProfile(
    name="experiential",
    category_weights={
        'answerability': 0.5,       # Lower weight - doesn't need to answer questions
        'structured_data': 1.3,     # Higher weight - Event/Place schema important
        'authority': 0.9,           # Slightly lower - personal experience is valid
        'content_quality': 1.1,     # Standard+ - storytelling quality matters
        'citationability': 0.6,     # Much lower - not about facts/data
        'technical': 1.0            # Standard
    },
    adjustments={
        'allow_narrative_style': True,
        'value_imagery': True,
        'value_emotional_language': True,
        'prefer_event_place_schema': True,
        'min_word_count': 200,      # Lower requirement
        'prefer_storytelling': True
    }
)


# Transactional content (products, services, e-commerce)
TRANSACTIONAL_PROFILE = ScoringProfile(
    name="transactional",
    category_weights={
        'answerability': 0.8,       # Lower - more about specs than Q&A
        'structured_data': 1.4,     # Highest - Product/Offer schema critical
        'authority': 1.1,           # Important - trust in commerce
        'content_quality': 0.9,     # Slightly lower - concise is better
        'citationability': 0.7,     # Lower - not primarily informational
        'technical': 1.2            # Higher - performance matters in e-commerce
    },
    adjustments={
        'require_product_schema': True,
        'value_reviews': True,
        'value_pricing_clarity': True,
        'value_cta': True,
        'min_word_count': 100       # Much lower - concise product descriptions
    }
)


# Navigational content (category pages, hubs, indices)
NAVIGATIONAL_PROFILE = ScoringProfile(
    name="navigational",
    category_weights={
        'answerability': 0.6,       # Lower - navigation focused
        'structured_data': 1.2,     # Important - breadcrumbs, sitemaps
        'authority': 0.8,           # Less critical
        'content_quality': 0.7,     # Less content expected
        'citationability': 0.5,     # Not applicable
        'technical': 1.3            # Higher - UX and performance critical
    },
    adjustments={
        'allow_thin_content': True,
        'value_link_structure': True,
        'value_breadcrumbs': True,
        'min_word_count': 50        # Very low - navigation pages are brief
    }
)


# Profile registry
PROFILES = {
    INFORMATIONAL: INFORMATIONAL_PROFILE,
    EXPERIENTIAL: EXPERIENTIAL_PROFILE,
    TRANSACTIONAL: TRANSACTIONAL_PROFILE,
    NAVIGATIONAL: NAVIGATIONAL_PROFILE,
    'default': DEFAULT_PROFILE
}


def get_profile(content_type: str) -> ScoringProfile:
    """
    Get scoring profile for content type
    
    Args:
        content_type: Content type from classifier
        
    Returns:
        Appropriate scoring profile
    """
    return PROFILES.get(content_type, DEFAULT_PROFILE)


def get_profile_by_name(name: str) -> ScoringProfile:
    """Get profile by name (alias for get_profile)"""
    return get_profile(name)

