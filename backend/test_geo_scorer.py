"""
GEO Scorer Test Cases

Tests the GEO scoring model with three different brand types:
1. Luxury experiential brand (Aprisio-like)
2. SaaS documentation-heavy product
3. Content publisher/blog network
"""

from scoring.geo_scorer import GEOScorer
import json


def test_luxury_experiential_brand():
    """Test Case 1: Luxury Experiential Brand (like Aprisio)"""
    
    scorer = GEOScorer()
    
    site_data = {
        'siteUrl': 'https://aprisio.com',
        'pages': [
            {
                'url': 'https://aprisio.com/',
                'html': '<html>...</html>',
                'aeoscore': 68,
                'pageIntent': 'NAVIGATIONAL',
                'pageSummary': 'Aprisio curates unique experiences for discerning travelers',
                'authoritySignals': {'hasAuthor': False, 'hasOrgSchema': True, 'hasDates': False}
            },
            {
                'url': 'https://aprisio.com/experiences/the-art-of-the-pour',
                'html': '<html>...</html>',
                'aeoscore': 72,
                'pageIntent': 'EXPERIENTIAL',
                'pageSummary': 'Aprisio presents an immersive coffee tasting journey exploring the art of the pour',
                'authoritySignals': {'hasAuthor': True, 'hasOrgSchema': False, 'hasDates': True}
            },
            {
                'url': 'https://aprisio.com/experiences/back-in-time-rock',
                'html': '<html>...</html>',
                'aeoscore': 70,
                'pageIntent': 'EXPERIENTIAL',
                'pageSummary': 'Travel back in time with Aprisio for an authentic rock music experience',
                'authoritySignals': {'hasAuthor': True, 'hasOrgSchema': False, 'hasDates': True}
            },
            {
                'url': 'https://aprisio.com/experiences/tea-odyssey',
                'html': '<html>...</html>',
                'aeoscore': 69,
                'pageIntent': 'EXPERIENTIAL',
                'pageSummary': 'Aprisio invites you on a tea odyssey through rare blends and traditions',
                'authoritySignals': {'hasAuthor': True, 'hasOrgSchema': False, 'hasDates': True}
            },
            {
                'url': 'https://aprisio.com/blog/curating-experiences',
                'html': '<html>...</html>',
                'aeoscore': 65,
                'pageIntent': 'KNOWLEDGE',
                'pageSummary': 'How Aprisio curates unique cultural experiences for modern travelers',
                'authoritySignals': {'hasAuthor': True, 'hasOrgSchema': False, 'hasDates': True}
            }
        ]
    }
    
    result = scorer.calculate_geo_score(site_data)
    
    print("=" * 80)
    print("TEST CASE 1: LUXURY EXPERIENTIAL BRAND (Aprisio-like)")
    print("=" * 80)
    print(json.dumps(result, indent=2))
    print("\n✓ Expected: Mid-range score (50-70) due to experiential focus")
    print(f"✓ Actual: {result['geo_score']}/100")
    print()
    
    return result


def test_saas_documentation():
    """Test Case 2: SaaS Documentation-Heavy Product"""
    
    scorer = GEOScorer()
    
    site_data = {
        'siteUrl': 'https://techsaas.io',
        'html': '<html>...</html>',
        'pages': [
            {
                'url': 'https://techsaas.io/',
                'html': '<html>...</html>',
                'aeoscore': 75,
                'pageIntent': 'TRANSACTIONAL',
                'pageSummary': 'TechSaaS provides cloud infrastructure management for enterprises',
                'authoritySignals': {'hasAuthor': False, 'hasOrgSchema': True, 'hasDates': False}
            },
            {
                'url': 'https://techsaas.io/about',
                'html': '<html>...</html>',
                'aeoscore': 78,
                'pageIntent': 'KNOWLEDGE',
                'pageSummary': 'TechSaaS is a leading cloud infrastructure platform founded in 2020',
                'authoritySignals': {'hasAuthor': True, 'hasOrgSchema': True, 'hasDates': True}
            },
            {
                'url': 'https://techsaas.io/docs/getting-started',
                'html': '<html>...</html>',
                'aeoscore': 82,
                'pageIntent': 'KNOWLEDGE',
                'pageSummary': 'Getting started with TechSaaS: complete guide to setup and configuration',
                'authoritySignals': {'hasAuthor': True, 'hasOrgSchema': False, 'hasDates': True}
            },
            {
                'url': 'https://techsaas.io/docs/api-reference',
                'html': '<html>...</html>',
                'aeoscore': 85,
                'pageIntent': 'KNOWLEDGE',
                'pageSummary': 'TechSaaS API reference documentation for developers',
                'authoritySignals': {'hasAuthor': True, 'hasOrgSchema': False, 'hasDates': True}
            },
            {
                'url': 'https://techsaas.io/docs/best-practices',
                'html': '<html>...</html>',
                'aeoscore': 80,
                'pageIntent': 'KNOWLEDGE',
                'pageSummary': 'Best practices for deploying with TechSaaS in production',
                'authoritySignals': {'hasAuthor': True, 'hasOrgSchema': False, 'hasDates': True}
            },
            {
                'url': 'https://techsaas.io/blog/vs-competitors',
                'html': '<html>...</html>',
                'aeoscore': 79,
                'pageIntent': 'KNOWLEDGE',
                'pageSummary': 'TechSaaS vs competitors: comprehensive comparison guide',
                'authoritySignals': {'hasAuthor': True, 'hasOrgSchema': False, 'hasDates': True}
            },
            {
                'url': 'https://techsaas.io/guides/scaling',
                'html': '<html>...</html>',
                'aeoscore': 81,
                'pageIntent': 'KNOWLEDGE',
                'pageSummary': 'How to scale applications with TechSaaS: complete guide',
                'authoritySignals': {'hasAuthor': True, 'hasOrgSchema': False, 'hasDates': True}
            }
        ]
    }
    
    result = scorer.calculate_geo_score(site_data)
    
    print("=" * 80)
    print("TEST CASE 2: SAAS DOCUMENTATION-HEAVY PRODUCT")
    print("=" * 80)
    print(json.dumps(result, indent=2))
    print("\n✓ Expected: High score (65-80) due to strong knowledge foundation")
    print(f"✓ Actual: {result['geo_score']}/100")
    print()
    
    return result


def test_thin_content_publisher():
    """Test Case 3: Thin Content Publisher (should score low)"""
    
    scorer = GEOScorer()
    
    site_data = {
        'siteUrl': 'https://quickblog.net',
        'pages': [
            {
                'url': 'https://quickblog.net/',
                'html': '<html>...</html>',
                'aeoscore': 25,
                'pageIntent': 'NAVIGATIONAL',
                'pageSummary': 'Latest news and updates',
                'authoritySignals': {'hasAuthor': False, 'hasOrgSchema': False, 'hasDates': False}
            },
            {
                'url': 'https://quickblog.net/post/1',
                'html': '<html>...</html>',
                'aeoscore': 22,
                'pageIntent': 'KNOWLEDGE',
                'pageSummary': 'Quick tips for success',
                'authoritySignals': {'hasAuthor': False, 'hasOrgSchema': False, 'hasDates': False}
            },
            {
                'url': 'https://quickblog.net/post/2',
                'html': '<html>...</html>',
                'aeoscore': 20,
                'pageIntent': 'KNOWLEDGE',
                'pageSummary': 'Top 5 trends to watch',
                'authoritySignals': {'hasAuthor': False, 'hasOrgSchema': False, 'hasDates': False}
            }
        ]
    }
    
    result = scorer.calculate_geo_score(site_data)
    
    print("=" * 80)
    print("TEST CASE 3: THIN CONTENT PUBLISHER")
    print("=" * 80)
    print(json.dumps(result, indent=2))
    print("\n✓ Expected: Low score (<40) due to thin content and weak signals")
    print(f"✓ Actual: {result['geo_score']}/100")
    print()
    
    return result


if __name__ == "__main__":
    print("\n🧪 GEO SCORER TEST SUITE\n")
    
    # Run all tests
    result1 = test_luxury_experiential_brand()
    result2 = test_saas_documentation()
    result3 = test_thin_content_publisher()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"1. Luxury Experiential Brand: {result1['geo_score']}/100 - {'✓ PASS' if 50 <= result1['geo_score'] <= 75 else '✗ FAIL'}")
    print(f"2. SaaS Documentation: {result2['geo_score']}/100 - {'✓ PASS' if 65 <= result2['geo_score'] <= 85 else '✗ FAIL'}")
    print(f"3. Thin Content Publisher: {result3['geo_score']}/100 - {'✓ PASS' if result3['geo_score'] < 40 else '✗ FAIL'}")
    print()

