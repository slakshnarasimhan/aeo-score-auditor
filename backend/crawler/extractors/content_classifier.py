"""
Content Type Classifier - Determines the intent/type of a page
"""
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from loguru import logger


class ContentClassifier:
    """Classifies content into types for context-aware scoring"""
    
    # Content type definitions
    INFORMATIONAL = "informational"  # How-to, guides, articles, educational
    EXPERIENTIAL = "experiential"    # Experiences, stories, events, travel
    TRANSACTIONAL = "transactional"  # Products, services, bookings
    NAVIGATIONAL = "navigational"    # Category pages, hubs, indices
    
    # Schema.org type mappings
    SCHEMA_TYPE_MAP = {
        # Informational
        'Article': INFORMATIONAL,
        'BlogPosting': INFORMATIONAL,
        'NewsArticle': INFORMATIONAL,
        'HowTo': INFORMATIONAL,
        'FAQPage': INFORMATIONAL,
        'QAPage': INFORMATIONAL,
        'TechArticle': INFORMATIONAL,
        'ScholarlyArticle': INFORMATIONAL,
        
        # Experiential
        'Event': EXPERIENTIAL,
        'Place': EXPERIENTIAL,
        'TouristAttraction': EXPERIENTIAL,
        'LodgingBusiness': EXPERIENTIAL,
        'Restaurant': EXPERIENTIAL,
        'LocalBusiness': EXPERIENTIAL,
        'TravelAction': EXPERIENTIAL,
        'Trip': EXPERIENTIAL,
        
        # Transactional
        'Product': TRANSACTIONAL,
        'Offer': TRANSACTIONAL,
        'Service': TRANSACTIONAL,
        'Order': TRANSACTIONAL,
        
        # Navigational
        'CollectionPage': NAVIGATIONAL,
        'ItemList': NAVIGATIONAL,
        'WebSite': NAVIGATIONAL,
    }
    
    # Keyword patterns for heuristic detection
    EXPERIENTIAL_KEYWORDS = [
        'experience', 'journey', 'story', 'adventure', 'explore', 'discover',
        'visit', 'tour', 'trip', 'travel', 'event', 'celebration', 'memories',
        'atmosphere', 'ambiance', 'immerse', 'feel', 'sense', 'witness'
    ]
    
    INFORMATIONAL_KEYWORDS = [
        'how to', 'guide', 'tutorial', 'learn', 'understand', 'explain',
        'definition', 'what is', 'why', 'when', 'steps', 'tips', 'advice',
        'faq', 'question', 'answer', 'help', 'instruction'
    ]
    
    TRANSACTIONAL_KEYWORDS = [
        'buy', 'purchase', 'price', 'cost', 'order', 'cart', 'checkout',
        'add to cart', 'book now', 'reserve', 'subscription', 'plan',
        'shipping', 'delivery', 'payment', 'discount', 'sale'
    ]
    
    def __init__(self, soup: BeautifulSoup, jsonld: List[Dict], url: str):
        """
        Initialize classifier
        
        Args:
            soup: BeautifulSoup parsed HTML
            jsonld: List of JSON-LD blocks
            url: Page URL
        """
        self.soup = soup
        self.jsonld = jsonld
        self.url = url
    
    def classify(self) -> Dict:
        """
        Classify content type using multiple signals
        
        Returns:
            Dict with type, confidence, and signals used
        """
        signals = []
        scores = {
            self.INFORMATIONAL: 0,
            self.EXPERIENTIAL: 0,
            self.TRANSACTIONAL: 0,
            self.NAVIGATIONAL: 0
        }
        
        # Signal 1: Explicit meta tag (highest priority)
        meta_type = self._check_meta_tag()
        if meta_type:
            signals.append(f"meta_tag:{meta_type}")
            return {
                'type': meta_type,
                'confidence': 'high',
                'primary_signal': 'explicit_meta_tag',
                'all_signals': signals,
                'description': self._get_type_description(meta_type)
            }
        
        # Signal 2: Schema.org types
        schema_type = self._check_schema_types()
        if schema_type:
            signals.append(f"schema:{schema_type}")
            scores[schema_type] += 3  # Strong signal
        
        # Signal 3: URL patterns
        url_type = self._check_url_patterns()
        if url_type:
            signals.append(f"url:{url_type}")
            scores[url_type] += 1
        
        # Signal 4: Content heuristics
        heuristic_scores = self._analyze_content_heuristics()
        for content_type, score in heuristic_scores.items():
            if score > 0:
                signals.append(f"heuristic:{content_type}:{score}")
                scores[content_type] += score
        
        # Signal 5: Structural patterns
        structure_type = self._check_structural_patterns()
        if structure_type:
            signals.append(f"structure:{structure_type}")
            scores[structure_type] += 1
        
        # Determine final type and confidence
        if max(scores.values()) == 0:
            # No clear signals, default to informational
            final_type = self.INFORMATIONAL
            confidence = 'low'
        else:
            final_type = max(scores, key=scores.get)
            max_score = scores[final_type]
            confidence = 'high' if max_score >= 3 else 'medium' if max_score >= 2 else 'low'
        
        logger.info(f"Content classified as {final_type} (confidence: {confidence})")
        logger.debug(f"Scores: {scores}, Signals: {signals}")
        
        return {
            'type': final_type,
            'confidence': confidence,
            'primary_signal': signals[0] if signals else 'default',
            'all_signals': signals,
            'scores': scores,
            'description': self._get_type_description(final_type)
        }
    
    def _check_meta_tag(self) -> Optional[str]:
        """Check for explicit content type declaration"""
        # Check custom meta tag
        meta = self.soup.find('meta', attrs={'name': 'aeo:content-type'})
        if meta and meta.get('content'):
            content_type = meta.get('content').lower()
            if content_type in [self.INFORMATIONAL, self.EXPERIENTIAL, 
                               self.TRANSACTIONAL, self.NAVIGATIONAL]:
                logger.info(f"Found explicit content type: {content_type}")
                return content_type
        return None
    
    def _check_schema_types(self) -> Optional[str]:
        """Check JSON-LD schema types"""
        for block in self.jsonld:
            schema_type = block.get('@type')
            if isinstance(schema_type, list):
                schema_type = schema_type[0]
            
            if schema_type in self.SCHEMA_TYPE_MAP:
                return self.SCHEMA_TYPE_MAP[schema_type]
        return None
    
    def _check_url_patterns(self) -> Optional[str]:
        """Analyze URL for content type hints"""
        url_lower = self.url.lower()
        
        # Experiential patterns
        if any(pattern in url_lower for pattern in [
            '/experience', '/event', '/tour', '/visit', '/trip', '/travel',
            '/attraction', '/place', '/story', '/journey'
        ]):
            return self.EXPERIENTIAL
        
        # Transactional patterns
        if any(pattern in url_lower for pattern in [
            '/product', '/shop', '/store', '/buy', '/pricing', '/plans',
            '/checkout', '/cart'
        ]):
            return self.TRANSACTIONAL
        
        # Informational patterns
        if any(pattern in url_lower for pattern in [
            '/blog', '/article', '/guide', '/how-to', '/tutorial', '/faq',
            '/help', '/learn', '/docs', '/wiki'
        ]):
            return self.INFORMATIONAL
        
        # Navigational patterns
        if any(pattern in url_lower for pattern in [
            '/category', '/archive', '/index', '/sitemap'
        ]):
            return self.NAVIGATIONAL
        
        return None
    
    def _analyze_content_heuristics(self) -> Dict[str, int]:
        """Analyze content for type-specific keywords and patterns"""
        scores = {
            self.INFORMATIONAL: 0,
            self.EXPERIENTIAL: 0,
            self.TRANSACTIONAL: 0,
            self.NAVIGATIONAL: 0
        }
        
        # Get text content
        text = self.soup.get_text().lower()
        
        # Count keyword occurrences
        for keyword in self.EXPERIENTIAL_KEYWORDS:
            scores[self.EXPERIENTIAL] += text.count(keyword)
        
        for keyword in self.INFORMATIONAL_KEYWORDS:
            scores[self.INFORMATIONAL] += text.count(keyword)
        
        for keyword in self.TRANSACTIONAL_KEYWORDS:
            scores[self.TRANSACTIONAL] += text.count(keyword)
        
        # Normalize scores (cap at 3 for balance)
        for key in scores:
            scores[key] = min(scores[key] // 3, 3)
        
        return scores
    
    def _check_structural_patterns(self) -> Optional[str]:
        """Analyze page structure for patterns"""
        # Experiential: Heavy on images, galleries, videos
        images = len(self.soup.find_all('img'))
        videos = len(self.soup.find_all(['video', 'iframe']))
        if images + videos > 10:
            return self.EXPERIENTIAL
        
        # Transactional: Forms, buttons, pricing
        forms = len(self.soup.find_all('form'))
        buttons = len(self.soup.find_all('button'))
        if forms > 0 or buttons > 5:
            # Check for transactional keywords in buttons
            button_text = ' '.join([btn.get_text().lower() for btn in self.soup.find_all('button')])
            if any(word in button_text for word in ['buy', 'add to cart', 'checkout', 'book']):
                return self.TRANSACTIONAL
        
        # Informational: Lists, headings, paragraphs
        headings = len(self.soup.find_all(['h1', 'h2', 'h3']))
        lists = len(self.soup.find_all(['ol', 'ul']))
        if headings > 5 and lists > 3:
            return self.INFORMATIONAL
        
        # Navigational: Many links, categories
        links = len(self.soup.find_all('a'))
        if links > 50:
            return self.NAVIGATIONAL
        
        return None
    
    def _get_type_description(self, content_type: str) -> str:
        """Get human-readable description of content type"""
        descriptions = {
            self.INFORMATIONAL: "Educational content that answers questions and provides information",
            self.EXPERIENTIAL: "Experience-focused content that tells stories and evokes emotion",
            self.TRANSACTIONAL: "Commerce-focused content for products and services",
            self.NAVIGATIONAL: "Hub or index page for navigation and discovery"
        }
        return descriptions.get(content_type, "Unknown content type")


def classify_content(soup: BeautifulSoup, jsonld: List[Dict], url: str) -> Dict:
    """Convenience function to classify content"""
    classifier = ContentClassifier(soup, jsonld, url)
    return classifier.classify()

