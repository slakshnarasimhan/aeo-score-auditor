"""
Complete audit pipeline that orchestrates all components
"""
from typing import Dict, List
from loguru import logger

from crawler.orchestrator import ExtractionOrchestrator
from scoring.calculator import AEOScoreCalculator


class AuditPipeline:
    """Main audit pipeline"""
    
    def __init__(self):
        self.orchestrator = ExtractionOrchestrator()
        self.calculator = AEOScoreCalculator()
    
    async def audit_page(self, url: str, options: Dict = None) -> Dict:
        """
        Complete page audit
        
        Args:
            url: URL to audit
            options: Audit options
            
        Returns:
            Complete audit results with scores
        """
        options = options or {}
        
        logger.info(f"Starting audit pipeline for: {url}")
        
        try:
            # Step 1: Extract data
            logger.info("Step 1/3: Extracting page data...")
            extracted_data = await self.orchestrator.extract(url)
            
            # Step 2: Calculate scores
            logger.info("Step 2/3: Calculating scores...")
            scores = self.calculator.calculate_score(extracted_data)
            
            # Step 3: Generate recommendations (simplified for now)
            logger.info("Step 3/3: Generating recommendations...")
            recommendations = self._generate_simple_recommendations(extracted_data, scores)
            
            # Combine results
            result = {
                'url': url,
                'overall_score': scores['overall_score'],
                'grade': scores['grade'],
                'breakdown': scores['breakdown'],
                'recommendations': recommendations,
                'extracted_data': {
                    'word_count': extracted_data.word_count,
                    'heading_count': len(extracted_data.headings),
                    'question_count': len(extracted_data.questions),
                    'jsonld_count': len(extracted_data.jsonld),
                    'has_author': extracted_data.author.get('found', False),
                    'has_dates': bool(extracted_data.dates.get('published'))
                }
            }
            
            # Include content classification if available
            if 'content_classification' in scores:
                result['content_classification'] = scores['content_classification']
            
            logger.info(f"Audit complete for: {url} - Score: {scores['overall_score']}")
            return result
            
        except Exception as e:
            logger.error(f"Audit failed for {url}: {e}")
            raise
    
    def _generate_simple_recommendations(self, data, scores: Dict) -> List[Dict]:
        """Generate basic recommendations based on gaps"""
        recommendations = []
        
        # Check each category for gaps
        for category, score_data in scores['breakdown'].items():
            score = score_data['score']
            max_score = score_data['max']
            gap = max_score - score
            
            if gap >= 2:  # Significant gap
                recommendations.append({
                    'category': category,
                    'title': f"Improve {category.replace('_', ' ').title()}",
                    'current_score': score,
                    'max_score': max_score,
                    'potential_gain': gap,
                    'priority': int((gap / max_score) * 100)
                })
        
        # Sort by priority
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        
        return recommendations[:10]  # Top 10


# Convenience function
async def audit_url(url: str, options: Dict = None) -> Dict:
    """Convenience function to audit a URL"""
    pipeline = AuditPipeline()
    return await pipeline.audit_page(url, options)

