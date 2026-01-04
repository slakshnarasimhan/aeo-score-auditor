"""
GEO (Generative Engine Optimization) Scorer

Evaluates brand-level inclusion readiness for generative AI systems
(ChatGPT, Gemini, Perplexity) based on site structure, consistency,
coverage, and trust signals.

GEO Score (0-100) = 
  Brand Knowledge Foundation (30)
  + Topic Ownership & Coverage (25)
  + Cross-Page Consistency (20)
  + AI Recall Signals (15)
  + Contextual Trust Signals (10)
"""

from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter
import re
from loguru import logger


class GEOScorer:
    """Evaluates brand-level GEO readiness"""
    
    def __init__(self):
        self.max_scores = {
            'brand_foundation': 30,
            'topic_coverage': 25,
            'consistency': 20,
            'ai_recall': 15,
            'trust': 10
        }
    
    def calculate_geo_score(self, site_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate GEO score for a brand/site
        
        Args:
            site_data: {
                'siteUrl': str,
                'pages': List[{
                    'url': str,
                    'html': str,
                    'aeoscore': float,
                    'pageIntent': str,  # KNOWLEDGE, EXPERIENTIAL, TRANSACTIONAL, NAVIGATIONAL
                    'pageSummary': str,
                    'authoritySignals': {
                        'hasAuthor': bool,
                        'hasOrgSchema': bool,
                        'hasDates': bool
                    }
                }]
            }
            
        Returns:
            GEO score breakdown with evidence
        """
        site_url = site_data.get('siteUrl', '')
        pages = site_data.get('pages', [])
        
        if not pages:
            return self._empty_score("No pages provided")
        
        logger.info(f"Calculating GEO score for {site_url} ({len(pages)} pages)")
        
        # Extract brand name from site URL
        brand_name = self._extract_brand_name(site_url)
        
        # Calculate each component
        brand_foundation = self._score_brand_foundation(pages, brand_name)
        topic_coverage = self._score_topic_coverage(pages, brand_name)
        consistency = self._score_consistency(pages, brand_name)
        ai_recall = self._score_ai_recall(pages, brand_name)
        trust = self._score_trust(pages, site_url)
        
        # Calculate total
        geo_score = (
            brand_foundation['score'] +
            topic_coverage['score'] +
            consistency['score'] +
            ai_recall['score'] +
            trust['score']
        )
        
        # Generate summary and recommendations
        summary = self._generate_summary(pages, {
            'brand_foundation': brand_foundation,
            'topic_coverage': topic_coverage,
            'consistency': consistency,
            'ai_recall': ai_recall,
            'trust': trust
        }, brand_name)
        
        recommendations = self._generate_recommendations({
            'brand_foundation': brand_foundation,
            'topic_coverage': topic_coverage,
            'consistency': consistency,
            'ai_recall': ai_recall,
            'trust': trust
        })
        
        result = {
            'geo_score': round(geo_score, 1),
            'components': {
                'brand_foundation': brand_foundation,
                'topic_coverage': topic_coverage,
                'consistency': consistency,
                'ai_recall': ai_recall,
                'trust': trust
            },
            'summary': summary,
            'recommended_actions': recommendations,
            'brand_name': brand_name,
            'pages_analyzed': len(pages)
        }
        
        logger.info(f"GEO score: {geo_score:.1f}/100 for {brand_name}")
        return result
    
    def _extract_brand_name(self, site_url: str) -> str:
        """Extract brand name from URL"""
        # Remove protocol and www
        name = re.sub(r'^https?://(www\.)?', '', site_url)
        # Extract domain name
        name = name.split('/')[0].split('.')[0]
        return name.capitalize()
    
    def _score_brand_foundation(self, pages: List[Dict], brand_name: str) -> Dict[str, Any]:
        """
        Component 1: Brand Knowledge Foundation (30 points)
        
        Measures whether an AI can define the brand clearly.
        """
        score = 0
        evidence = []
        max_score = self.max_scores['brand_foundation']
        
        # Signal 1: Canonical "What is X?" page (10 points)
        has_canonical = False
        for page in pages:
            url_lower = page['url'].lower()
            summary_lower = page.get('pageSummary', '').lower()
            
            # Check for about/who/what pages
            if any(pattern in url_lower for pattern in ['/about', '/who-we-are', '/what-is']):
                has_canonical = True
                score += 10
                evidence.append(f"Found canonical brand page: {page['url']}")
                break
            
            # Check for brand definition in summary
            if brand_name.lower() in summary_lower and ('about' in summary_lower or 'what is' in summary_lower):
                has_canonical = True
                score += 8
                evidence.append(f"Found brand definition content: {page['url']}")
                break
        
        if not has_canonical:
            evidence.append("Missing: No clear 'About' or brand definition page found")
        
        # Signal 2: Organization schema presence (8 points)
        org_schema_count = sum(
            1 for p in pages 
            if p.get('authoritySignals', {}).get('hasOrgSchema', False)
        )
        if org_schema_count > 0:
            schema_score = min(8, org_schema_count * 4)
            score += schema_score
            evidence.append(f"Organization schema on {org_schema_count} page(s)")
        else:
            evidence.append("Missing: No Organization schema markup found")
        
        # Signal 3: Consistent brand mentions (7 points)
        brand_mention_count = sum(
            1 for p in pages
            if brand_name.lower() in p.get('pageSummary', '').lower()
        )
        mention_ratio = brand_mention_count / len(pages) if pages else 0
        mention_score = int(mention_ratio * 7)
        score += mention_score
        evidence.append(f"Brand mentioned in {brand_mention_count}/{len(pages)} pages ({mention_ratio*100:.0f}%)")
        
        # Signal 4: Knowledge-intent pages (5 points)
        knowledge_pages = [p for p in pages if p.get('pageIntent') == 'KNOWLEDGE']
        if len(knowledge_pages) >= 5:
            knowledge_score = 5
            score += knowledge_score
            evidence.append(f"{len(knowledge_pages)} knowledge-focused pages")
        elif len(knowledge_pages) >= 3:
            knowledge_score = 4
            score += knowledge_score
            evidence.append(f"{len(knowledge_pages)} knowledge-focused pages")
        elif len(knowledge_pages) >= 1:
            knowledge_score = 2
            score += knowledge_score
            evidence.append(f"{len(knowledge_pages)} knowledge page(s)")
        else:
            evidence.append("Missing: No knowledge-focused pages (e.g., guides, FAQs)")
        
        return {
            'score': round(min(score, max_score), 1),
            'max': max_score,
            'evidence': evidence
        }
    
    def _score_topic_coverage(self, pages: List[Dict], brand_name: str) -> Dict[str, Any]:
        """
        Component 2: Topic Ownership & Coverage (25 points)
        
        Measures whether the brand covers its expected topic space.
        """
        score = 0
        evidence = []
        max_score = self.max_scores['topic_coverage']
        
        # Extract topics from page summaries and URLs
        topics = self._extract_topics(pages)
        
        # Signal 1: Topic diversity (10 points)
        unique_topics = len(topics)
        if unique_topics >= 8:
            score += 10
            evidence.append(f"Strong topic coverage: {unique_topics} distinct topics")
        elif unique_topics >= 5:
            score += 7
            evidence.append(f"Good topic coverage: {unique_topics} distinct topics")
        elif unique_topics >= 3:
            score += 4
            evidence.append(f"Moderate topic coverage: {unique_topics} topics")
        else:
            score += 2
            evidence.append(f"Limited topic coverage: Only {unique_topics} topics")
        
        # Signal 2: Topic depth (hub + spokes) (10 points)
        topic_depth_score, depth_evidence = self._analyze_topic_depth(pages, topics)
        score += topic_depth_score
        evidence.extend(depth_evidence)
        
        # Signal 3: Intent mix (5 points)
        intent_distribution = Counter(p.get('pageIntent', 'UNKNOWN') for p in pages)
        has_knowledge = intent_distribution.get('KNOWLEDGE', 0) > 0
        has_experiential = intent_distribution.get('EXPERIENTIAL', 0) > 0
        
        if has_knowledge and has_experiential:
            score += 5
            evidence.append("Balanced content mix: knowledge + experiential pages")
        elif has_knowledge:
            score += 3
            evidence.append("Knowledge-focused content (consider adding experiential)")
        elif has_experiential:
            score += 3
            evidence.append("Experience-focused content (consider adding knowledge anchors)")
        else:
            score += 1
            evidence.append("Limited intent diversity")
        
        return {
            'score': round(min(score, max_score), 1),
            'max': max_score,
            'evidence': evidence
        }
    
    def _extract_topics(self, pages: List[Dict]) -> List[str]:
        """Extract topic keywords from pages"""
        topics = set()
        
        for page in pages:
            url = page['url'].lower()
            summary = page.get('pageSummary', '').lower()
            
            # Extract from URL path segments
            path_segments = [s for s in url.split('/') if len(s) > 3 and s not in ['http:', 'https:', 'www']]
            topics.update(path_segments[:5])  # Limit to avoid noise
            
            # Extract from summary (simple keyword extraction)
            words = re.findall(r'\b[a-z]{4,}\b', summary)
            # Filter common words
            stop_words = {'this', 'that', 'with', 'from', 'have', 'been', 'were', 'said', 'each', 'which', 'their', 'about', 'would', 'there'}
            meaningful_words = [w for w in words if w not in stop_words]
            # Count frequency and take top ones
            word_counts = Counter(meaningful_words)
            top_words = [w for w, c in word_counts.most_common(10) if c > 1]
            topics.update(top_words)
        
        return list(topics)[:15]  # Return top 15 topics
    
    def _analyze_topic_depth(self, pages: List[Dict], topics: List[str]) -> Tuple[float, List[str]]:
        """Analyze topic depth (hub + spoke pattern)"""
        score = 0
        evidence = []
        
        # Group pages by topic
        topic_groups = defaultdict(list)
        for page in pages:
            url_lower = page['url'].lower()
            summary_lower = page.get('pageSummary', '').lower()
            
            for topic in topics:
                if topic in url_lower or topic in summary_lower:
                    topic_groups[topic].append(page)
        
        # Analyze depth
        multi_page_topics = {t: pages for t, pages in topic_groups.items() if len(pages) > 1}
        
        if multi_page_topics:
            avg_depth = sum(len(pages) for pages in multi_page_topics.values()) / len(multi_page_topics)
            if avg_depth >= 3:
                score = 10
                evidence.append(f"Excellent topic depth: {len(multi_page_topics)} topics with multiple pages")
            elif avg_depth >= 2:
                score = 7
                evidence.append(f"Good topic depth: {len(multi_page_topics)} topics with 2+ pages each")
            else:
                score = 4
                evidence.append(f"Moderate depth: {len(multi_page_topics)} topics reinforced")
        else:
            score = 2
            evidence.append("Weak: Most topics covered by single pages only")
        
        # Penalize orphan experiential pages
        experiential_pages = [p for p in pages if p.get('pageIntent') == 'EXPERIENTIAL']
        knowledge_pages = [p for p in pages if p.get('pageIntent') == 'KNOWLEDGE']
        
        if experiential_pages and not knowledge_pages:
            score = max(0, score - 2)
            evidence.append("⚠️ Experiential content lacks knowledge anchors")
        
        return score, evidence
    
    def _score_consistency(self, pages: List[Dict], brand_name: str) -> Dict[str, Any]:
        """
        Component 3: Cross-Page Consistency (20 points)
        
        Measures semantic consistency across pages.
        """
        score = 0
        evidence = []
        max_score = self.max_scores['consistency']
        
        if len(pages) < 2:
            return {
                'score': 10,  # Give benefit of doubt for single page
                'max': max_score,
                'evidence': ['Single page - consistency not applicable']
            }
        
        # Signal 1: Brand name consistency (8 points)
        brand_mentions = [
            brand_name.lower() in p.get('pageSummary', '').lower()
            for p in pages
        ]
        consistency_ratio = sum(brand_mentions) / len(pages)
        
        if consistency_ratio >= 0.8:
            score += 8
            evidence.append(f"Excellent brand consistency: {consistency_ratio*100:.0f}% of pages mention brand")
        elif consistency_ratio >= 0.5:
            score += 5
            evidence.append(f"Good brand consistency: {consistency_ratio*100:.0f}% of pages")
        else:
            score += 2
            evidence.append(f"Weak brand consistency: Only {consistency_ratio*100:.0f}% of pages mention brand")
        
        # Signal 2: Tone/voice consistency (7 points)
        # Simple heuristic: pages of same intent should have similar summary lengths
        intent_groups = defaultdict(list)
        for page in pages:
            intent = page.get('pageIntent', 'UNKNOWN')
            summary_len = len(page.get('pageSummary', ''))
            intent_groups[intent].append(summary_len)
        
        consistent_tone = True
        for intent, lengths in intent_groups.items():
            if len(lengths) > 1:
                avg_len = sum(lengths) / len(lengths)
                variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
                std_dev = variance ** 0.5
                if std_dev > avg_len * 0.5:  # High variance
                    consistent_tone = False
        
        if consistent_tone:
            score += 7
            evidence.append("Consistent content tone across pages")
        else:
            score += 4
            evidence.append("Moderate tone consistency (some variation detected)")
        
        # Signal 3: No contradictions (5 points)
        # Simple check: no extremely low AEO scores mixed with high ones
        aeo_scores = [p.get('aeoscore', 0) for p in pages]
        if aeo_scores:
            avg_aeo = sum(aeo_scores) / len(aeo_scores)
            outliers = [s for s in aeo_scores if abs(s - avg_aeo) > 30]
            
            if not outliers:
                score += 5
                evidence.append("No quality outliers - consistent standard")
            elif len(outliers) <= 1:
                score += 3
                evidence.append("Mostly consistent quality across pages")
            else:
                score += 1
                evidence.append(f"Quality inconsistency: {len(outliers)} outlier pages")
        
        return {
            'score': round(min(score, max_score), 1),
            'max': max_score,
            'evidence': evidence
        }
    
    def _score_ai_recall(self, pages: List[Dict], brand_name: str) -> Dict[str, Any]:
        """
        Component 4: AI Recall Signals (15 points)
        
        Estimates likelihood of implicit recall by LLMs.
        """
        score = 0
        evidence = []
        max_score = self.max_scores['ai_recall']
        
        # Signal 1: Comparative/list content (6 points)
        comparative_pages = []
        for page in pages:
            summary = page.get('pageSummary', '').lower()
            if any(word in summary for word in ['compare', 'vs', 'versus', 'best', 'top', 'list', 'guide']):
                comparative_pages.append(page['url'])
        
        if len(comparative_pages) >= 3:
            score += 6
            evidence.append(f"{len(comparative_pages)} pages with comparative/list content")
        elif len(comparative_pages) >= 1:
            score += 3
            evidence.append(f"{len(comparative_pages)} comparative pages")
        else:
            evidence.append("Missing: No comparative or list-style content")
        
        # Signal 2: Distinct brand naming (5 points)
        # Check if brand name is unique/memorable (not generic)
        generic_words = ['company', 'business', 'services', 'solutions', 'group', 'corp', 'inc']
        is_distinct = brand_name.lower() not in generic_words
        
        if is_distinct:
            score += 5
            evidence.append(f"Distinct brand name: '{brand_name}'")
        else:
            score += 2
            evidence.append(f"Generic brand name: '{brand_name}'")
        
        # Signal 3: Content that answers questions (4 points)
        question_answering = sum(
            1 for p in pages
            if p.get('pageIntent') == 'KNOWLEDGE' and p.get('aeoscore', 0) > 50
        )
        
        if question_answering >= 3:
            score += 4
            evidence.append(f"{question_answering} pages optimized for Q&A")
        elif question_answering >= 1:
            score += 2
            evidence.append(f"{question_answering} Q&A-style pages")
        else:
            evidence.append("Missing: No question-answering content")
        
        return {
            'score': round(min(score, max_score), 1),
            'max': max_score,
            'evidence': evidence
        }
    
    def _score_trust(self, pages: List[Dict], site_url: str) -> Dict[str, Any]:
        """
        Component 5: Contextual Trust Signals (10 points)
        
        Evaluates whether AI would feel safe including the brand.
        """
        score = 0
        evidence = []
        max_score = self.max_scores['trust']
        
        # Signal 1: HTTPS consistency (3 points)
        if 'localhost' not in site_url:
            if site_url.startswith('https://'):
                score += 3
                evidence.append("HTTPS enabled")
            else:
                evidence.append("⚠️ No HTTPS")
        else:
            score += 3
            evidence.append("Localhost (HTTPS check skipped)")
        
        # Signal 2: Author/ownership transparency (4 points)
        pages_with_authors = sum(
            1 for p in pages
            if p.get('authoritySignals', {}).get('hasAuthor', False)
        )
        author_ratio = pages_with_authors / len(pages) if pages else 0
        
        if author_ratio >= 0.5:
            score += 4
            evidence.append(f"Strong authorship: {pages_with_authors}/{len(pages)} pages")
        elif author_ratio >= 0.2:
            score += 2
            evidence.append(f"Partial authorship: {pages_with_authors}/{len(pages)} pages")
        else:
            evidence.append(f"Weak authorship: Only {pages_with_authors}/{len(pages)} pages")
        
        # Signal 3: Date transparency (3 points)
        pages_with_dates = sum(
            1 for p in pages
            if p.get('authoritySignals', {}).get('hasDates', False)
        )
        date_ratio = pages_with_dates / len(pages) if pages else 0
        
        if date_ratio >= 0.5:
            score += 3
            evidence.append(f"Dates on {pages_with_dates}/{len(pages)} pages")
        elif date_ratio >= 0.2:
            score += 2
            evidence.append(f"Some dates: {pages_with_dates}/{len(pages)} pages")
        else:
            evidence.append(f"Missing dates: Only {pages_with_dates}/{len(pages)} pages")
        
        return {
            'score': round(min(score, max_score), 1),
            'max': max_score,
            'evidence': evidence
        }
    
    def _generate_summary(self, pages: List[Dict], components: Dict, brand_name: str) -> str:
        """Generate human-readable summary"""
        total_score = sum(c['score'] for c in components.values())
        
        # Determine primary content type
        intent_counts = Counter(p.get('pageIntent') for p in pages)
        primary_intent = intent_counts.most_common(1)[0][0] if intent_counts else 'UNKNOWN'
        
        # Assess strengths and weaknesses
        strengths = []
        weaknesses = []
        
        for name, comp in components.items():
            percentage = (comp['score'] / comp['max']) * 100
            if percentage >= 70:
                strengths.append(name.replace('_', ' '))
            elif percentage < 40:
                weaknesses.append(name.replace('_', ' '))
        
        # Build summary
        if total_score >= 70:
            tone = "excellent"
        elif total_score >= 50:
            tone = "strong"
        elif total_score >= 30:
            tone = "moderate"
        else:
            tone = "limited"
        
        summary_parts = [f"{brand_name} shows {tone} GEO readiness"]
        
        if primary_intent == 'EXPERIENTIAL':
            summary_parts.append("with a focus on experiential content")
        elif primary_intent == 'KNOWLEDGE':
            summary_parts.append("with strong knowledge-focused content")
        
        if strengths:
            summary_parts.append(f"particularly in {', '.join(strengths[:2])}")
        
        if weaknesses:
            summary_parts.append(f"but would benefit from improvements in {', '.join(weaknesses[:2])}")
        
        return '. '.join(summary_parts) + '.'
    
    def _generate_recommendations(self, components: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Brand foundation
        bf_pct = (components['brand_foundation']['score'] / components['brand_foundation']['max']) * 100
        if bf_pct < 60:
            recommendations.append("Create a canonical 'About' or brand definition page")
            recommendations.append("Add Organization schema markup across key pages")
        
        # Topic coverage
        tc_pct = (components['topic_coverage']['score'] / components['topic_coverage']['max']) * 100
        if tc_pct < 60:
            recommendations.append("Expand topic coverage with knowledge-style hub pages")
            recommendations.append("Create content clusters (hub + spoke) for key topics")
        
        # Consistency
        cons_pct = (components['consistency']['score'] / components['consistency']['max']) * 100
        if cons_pct < 60:
            recommendations.append("Improve brand name consistency across pages")
            recommendations.append("Standardize content quality and tone")
        
        # AI recall
        recall_pct = (components['ai_recall']['score'] / components['ai_recall']['max']) * 100
        if recall_pct < 60:
            recommendations.append("Add comparative/list-style content (e.g., 'Best X for Y')")
            recommendations.append("Create Q&A-focused pages for common queries")
        
        # Trust
        trust_pct = (components['trust']['score'] / components['trust']['max']) * 100
        if trust_pct < 60:
            recommendations.append("Add author information to content pages")
            recommendations.append("Include publication/update dates on all pages")
        
        # Cap at 5 recommendations
        return recommendations[:5]
    
    def _empty_score(self, reason: str) -> Dict[str, Any]:
        """Return empty score with reason"""
        return {
            'geo_score': 0,
            'components': {
                name: {'score': 0, 'max': max_val, 'evidence': [reason]}
                for name, max_val in self.max_scores.items()
            },
            'summary': reason,
            'recommended_actions': ['Provide page data to calculate GEO score'],
            'brand_name': 'Unknown',
            'pages_analyzed': 0
        }

