"""
Generate actionable recommendations for improving AEO scores
"""
from typing import Dict, List, Any


class RecommendationGenerator:
    """Generates specific, actionable recommendations based on audit scores"""
    
    def __init__(self):
        self.category_tips = self._initialize_category_tips()
    
    def _initialize_category_tips(self) -> Dict[str, Dict]:
        """Initialize detailed tips for each category and sub-category"""
        return {
            'answerability': {
                'title': 'Answerability',
                'description': 'How well your content directly answers user questions',
                'sub_categories': {
                    'direct_answer_presence': {
                        'title': 'Direct Answer Presence',
                        'low': [
                            'Add clear, direct answers at the beginning of your content',
                            'Use "The answer is..." or "Yes/No" patterns when appropriate',
                            'Create summary boxes or callout sections with key answers',
                            'Structure content with answer-first approach (inverted pyramid)'
                        ],
                        'medium': [
                            'Enhance existing answers with more specificity',
                            'Add featured snippets-friendly answer blocks (40-60 words)',
                            'Use definition lists (<dl>) for term-answer pairs'
                        ],
                        'high': [
                            'Maintain answer quality and freshness',
                            'Consider adding video/audio answers for complex topics'
                        ]
                    },
                    'question_coverage': {
                        'title': 'Question Coverage',
                        'low': [
                            'Research common questions in your topic using AnswerThePublic or Google\'s "People Also Ask"',
                            'Add FAQ section with 10+ relevant questions',
                            'Use question-style headings (H2/H3)',
                            'Address who, what, when, where, why, and how questions'
                        ],
                        'medium': [
                            'Expand FAQ with long-tail question variations',
                            'Add comparison questions ("X vs Y")',
                            'Include troubleshooting questions'
                        ],
                        'high': [
                            'Keep questions updated based on search trends',
                            'Add user-submitted questions section'
                        ]
                    },
                    'answer_conciseness': {
                        'title': 'Answer Conciseness',
                        'low': [
                            'Add TL;DR or summary sections',
                            'Break long paragraphs into shorter chunks (3-4 sentences max)',
                            'Use bullet points and numbered lists',
                            'Keep paragraphs under 100 words'
                        ],
                        'medium': [
                            'Add "Quick Answer" boxes for featured snippets',
                            'Use tables for comparison data',
                            'Add visual summaries (infographics, charts)'
                        ],
                        'high': [
                            'Optimize for voice search with 29-word answers',
                            'Test readability with Hemingway Editor'
                        ]
                    },
                    'answer_block_formatting': {
                        'title': 'Answer Block Formatting',
                        'low': [
                            'Use <blockquote> tags for highlighted answers',
                            'Add CSS styling for answer blocks (background color, borders)',
                            'Implement accordion/toggle for long answers',
                            'Use semantic HTML5 elements (<article>, <section>)'
                        ],
                        'medium': [
                            'Add icons or emojis for visual emphasis',
                            'Implement sticky/floating answer summaries',
                            'Use color coding for different answer types'
                        ],
                        'high': [
                            'A/B test different formatting styles',
                            'Add interactive elements (calculators, tools)'
                        ]
                    }
                }
            },
            'structured_data': {
                'title': 'Structured Data',
                'description': 'Schema.org markup that helps search engines understand your content',
                'sub_categories': {
                    'faq_schema': {
                        'title': 'FAQ Schema',
                        'low': [
                            'Add FAQPage schema with JSON-LD',
                            'Mark up at least 5 Q&A pairs',
                            'Use Google\'s Rich Results Test to validate',
                            'Follow schema.org/FAQPage guidelines'
                        ],
                        'medium': [
                            'Expand to 10+ FAQ items',
                            'Add acceptedAnswer with detailed text',
                            'Include question upvoteCount if applicable'
                        ],
                        'high': [
                            'Keep FAQ schema updated',
                            'Monitor rich results performance in Search Console'
                        ]
                    },
                    'howto_schema': {
                        'title': 'HowTo Schema',
                        'low': [
                            'Add HowTo schema for instructional content',
                            'Include step-by-step instructions with HowToStep',
                            'Add totalTime and supply/tool information',
                            'Include images for each step'
                        ],
                        'medium': [
                            'Add video instructions with VideoObject',
                            'Include tips and warnings in HowToTip/Direction',
                            'Add estimated cost information'
                        ],
                        'high': [
                            'Create video content for better engagement',
                            'Add user ratings and reviews'
                        ]
                    },
                    'article_schema': {
                        'title': 'Article Schema',
                        'low': [
                            'Add Article or BlogPosting schema',
                            'Include headline, datePublished, dateModified',
                            'Add author with Person schema',
                            'Include publisher with Organization schema and logo'
                        ],
                        'medium': [
                            'Add articleBody or articleSection',
                            'Include wordCount and image schema',
                            'Add breadcrumb schema for navigation'
                        ],
                        'high': [
                            'Implement SpeakableSpecification for voice search',
                            'Add AggregateRating if applicable'
                        ]
                    },
                    'breadcrumb_schema': {
                        'title': 'Breadcrumb Schema',
                        'low': [
                            'Add BreadcrumbList schema',
                            'Include all navigation levels',
                            'Use position property for ordering',
                            'Link to actual URLs with item.id'
                        ],
                        'medium': [
                            'Ensure breadcrumbs visible in UI',
                            'Add markup to all internal pages',
                            'Test with Rich Results Test'
                        ],
                        'high': [
                            'Monitor breadcrumb appearance in SERPs',
                            'A/B test breadcrumb styles'
                        ]
                    }
                }
            },
            'authority': {
                'title': 'Authority',
                'description': 'Trust signals and credibility indicators',
                'sub_categories': {
                    'author_info': {
                        'title': 'Author Information',
                        'low': [
                            'Add author bylines to all articles',
                            'Create author bio pages with credentials',
                            'Include author photos and contact info',
                            'Link to author social profiles (LinkedIn, Twitter)'
                        ],
                        'medium': [
                            'Add detailed author expertise and credentials',
                            'Include years of experience and education',
                            'List certifications and awards',
                            'Add author schema with sameAs links'
                        ],
                        'high': [
                            'Create comprehensive author portfolio pages',
                            'Get authors verified on social media',
                            'Publish author bylines on external sites'
                        ]
                    },
                    'citations': {
                        'title': 'Citations & Sources',
                        'low': [
                            'Add at least 3-5 external citations per article',
                            'Link to authoritative sources (.gov, .edu, established organizations)',
                            'Use inline citations with [1] notation',
                            'Add "References" or "Sources" section at bottom'
                        ],
                        'medium': [
                            'Cite academic papers and research studies',
                            'Link to primary sources, not secondary',
                            'Use rel="nofollow" for untrusted sources',
                            'Add publication dates to citations'
                        ],
                        'high': [
                            'Implement Citation schema markup',
                            'Update broken citation links regularly',
                            'Add DOI links for academic sources'
                        ]
                    },
                    'dates': {
                        'title': 'Date Information',
                        'low': [
                            'Add published date to all content',
                            'Show last updated/modified date prominently',
                            'Use <time> tag with datetime attribute',
                            'Include dates in schema markup (datePublished, dateModified)'
                        ],
                        'medium': [
                            'Add "Last Reviewed" dates for evergreen content',
                            'Show update history or changelog',
                            'Display dates near headline for visibility'
                        ],
                        'high': [
                            'Implement automated freshness updates',
                            'Add scheduled review reminders',
                            'Highlight recent updates in UI'
                        ]
                    },
                    'expertise_signals': {
                        'title': 'Expertise Signals',
                        'low': [
                            'Add "About" page with team credentials',
                            'Include editorial policy or methodology',
                            'Display contact information prominently',
                            'Add trust badges or certifications'
                        ],
                        'medium': [
                            'Get expert reviews or endorsements',
                            'Add case studies or portfolio work',
                            'Include client testimonials',
                            'Display industry memberships'
                        ],
                        'high': [
                            'Earn authoritative backlinks',
                            'Get featured in major publications',
                            'Speak at industry conferences'
                        ]
                    }
                }
            },
            'content_quality': {
                'title': 'Content Quality',
                'description': 'Depth, uniqueness, and value of your content',
                'sub_categories': {
                    'word_count': {
                        'title': 'Content Depth',
                        'low': [
                            'Expand content to at least 1000+ words for informational pages',
                            'Cover topic comprehensively (sub-topics, variations)',
                            'Add examples, case studies, or statistics',
                            'Include "Related Questions" sections'
                        ],
                        'medium': [
                            'Create pillar content (2000-3000+ words)',
                            'Add multimedia (images, videos, infographics)',
                            'Include expert quotes or interviews',
                            'Cover advanced and beginner aspects'
                        ],
                        'high': [
                            'Create ultimate guides (5000+ words)',
                            'Add original research or data',
                            'Include downloadable resources (PDFs, templates)'
                        ]
                    },
                    'headings': {
                        'title': 'Heading Structure',
                        'low': [
                            'Add H1 tag (only one per page)',
                            'Use H2 for main sections (at least 5-7)',
                            'Use H3 for sub-sections',
                            'Make headings descriptive and keyword-rich'
                        ],
                        'medium': [
                            'Follow proper hierarchy (don\'t skip levels)',
                            'Include questions in some headings',
                            'Front-load keywords in headings',
                            'Keep headings under 70 characters'
                        ],
                        'high': [
                            'A/B test heading variations',
                            'Optimize for featured snippet targeting',
                            'Add table of contents with jump links'
                        ]
                    },
                    'uniqueness': {
                        'title': 'Content Uniqueness',
                        'low': [
                            'Avoid duplicate content (check with Copyscape)',
                            'Add original insights or perspectives',
                            'Include personal experiences or examples',
                            'Write in unique brand voice'
                        ],
                        'medium': [
                            'Conduct original research or surveys',
                            'Create custom graphics and diagrams',
                            'Add expert commentary',
                            'Include data analysis or trends'
                        ],
                        'high': [
                            'Publish industry-first content',
                            'Create proprietary tools or calculators',
                            'Earn citations from other sites'
                        ]
                    },
                    'freshness': {
                        'title': 'Content Freshness',
                        'low': [
                            'Update content at least annually',
                            'Add current year to titles when relevant',
                            'Remove outdated information',
                            'Update statistics and data points'
                        ],
                        'medium': [
                            'Set up content review schedule',
                            'Add "What\'s New" sections',
                            'Update screenshots and examples',
                            'Revise for current best practices'
                        ],
                        'high': [
                            'Implement real-time data updates',
                            'Add trending topics sections',
                            'Monitor competitors for new angles'
                        ]
                    }
                }
            },
            'citationability': {
                'title': 'Citationability',
                'description': 'How easy it is for others to cite and reference your content',
                'sub_categories': {
                    'facts_density': {
                        'title': 'Facts & Data Density',
                        'low': [
                            'Add at least 10-15 factual statements per 1000 words',
                            'Include statistics with sources',
                            'Add data points and percentages',
                            'Use specific numbers instead of vague terms'
                        ],
                        'medium': [
                            'Create data visualizations (charts, graphs)',
                            'Add comparison tables',
                            'Include year-over-year trends',
                            'Provide downloadable datasets'
                        ],
                        'high': [
                            'Conduct original research studies',
                            'Publish annual industry reports',
                            'Create citation-worthy statistics'
                        ]
                    },
                    'tables': {
                        'title': 'Data Tables',
                        'low': [
                            'Add at least 2-3 data tables per article',
                            'Use <table> with proper <thead>, <tbody>',
                            'Make tables responsive/scrollable on mobile',
                            'Add descriptive <caption> to tables'
                        ],
                        'medium': [
                            'Add sortable columns with JavaScript',
                            'Include download options (CSV, Excel)',
                            'Add search/filter functionality',
                            'Use color coding for data visualization'
                        ],
                        'high': [
                            'Create interactive data explorers',
                            'Add real-time data updates',
                            'Implement Table schema markup'
                        ]
                    },
                    'clarity': {
                        'title': 'Content Clarity',
                        'low': [
                            'Use simple, clear language (8th-grade reading level)',
                            'Define technical terms on first use',
                            'Break complex ideas into steps',
                            'Use active voice over passive'
                        ],
                        'medium': [
                            'Add glossary for technical terms',
                            'Use analogies and metaphors',
                            'Include visual explanations',
                            'Test with readability tools'
                        ],
                        'high': [
                            'Add tooltips for complex terms',
                            'Create beginner-friendly summaries',
                            'Implement progressive disclosure'
                        ]
                    }
                }
            },
            'technical': {
                'title': 'Technical SEO',
                'description': 'Technical aspects affecting crawling and indexing',
                'sub_categories': {
                    'page_speed': {
                        'title': 'Page Speed',
                        'low': [
                            'Optimize images (compress, use WebP format)',
                            'Enable browser caching',
                            'Minify CSS, JavaScript, HTML',
                            'Use CDN for static assets'
                        ],
                        'medium': [
                            'Implement lazy loading for images',
                            'Remove render-blocking resources',
                            'Enable Gzip/Brotli compression',
                            'Reduce server response time (TTFB < 200ms)'
                        ],
                        'high': [
                            'Achieve Core Web Vitals targets (LCP < 2.5s, FID < 100ms, CLS < 0.1)',
                            'Implement HTTP/3 and QUIC',
                            'Use Edge computing for dynamic content'
                        ]
                    },
                    'mobile_friendly': {
                        'title': 'Mobile Friendliness',
                        'low': [
                            'Implement responsive design',
                            'Use viewport meta tag',
                            'Ensure text is readable without zooming (16px min)',
                            'Make buttons/links large enough (48x48px min)'
                        ],
                        'medium': [
                            'Test on real mobile devices',
                            'Optimize for touch interactions',
                            'Reduce mobile page weight',
                            'Use mobile-friendly navigation'
                        ],
                        'high': [
                            'Implement AMP or similar',
                            'Optimize for foldable devices',
                            'Test on slow 3G connections'
                        ]
                    },
                    'https': {
                        'title': 'HTTPS & Security',
                        'low': [
                            'Install SSL certificate',
                            'Redirect HTTP to HTTPS (301)',
                            'Update internal links to HTTPS',
                            'Fix mixed content warnings'
                        ],
                        'medium': [
                            'Implement HSTS header',
                            'Use strong cipher suites',
                            'Enable HTTP/2 or HTTP/3',
                            'Add security headers (CSP, X-Frame-Options)'
                        ],
                        'high': [
                            'Implement Certificate Transparency',
                            'Use OCSP stapling',
                            'Regular security audits'
                        ]
                    },
                    'crawlability': {
                        'title': 'Crawlability',
                        'low': [
                            'Create XML sitemap',
                            'Submit sitemap to Google Search Console',
                            'Fix robots.txt issues',
                            'Ensure important pages are linkable'
                        ],
                        'medium': [
                            'Optimize internal linking structure',
                            'Fix broken links (404s)',
                            'Add canonical tags',
                            'Implement proper URL structure'
                        ],
                        'high': [
                            'Monitor crawl budget',
                            'Implement IndexNow protocol',
                            'Use log file analysis'
                        ]
                    }
                }
            }
        }
    
    def generate_recommendations(self, scores: Dict[str, Any], top_n: int = 5) -> List[Dict]:
        """Generate top N recommendations based on score gaps"""
        recommendations = []
        
        breakdown = scores.get('breakdown', {})
        
        for category, score_data in breakdown.items():
            if category not in self.category_tips:
                continue
            
            score = score_data.get('score', 0)
            max_score = score_data.get('max', 100)
            percentage = score_data.get('percentage', 0)
            sub_scores = score_data.get('sub_scores', {})
            
            # Determine priority level based on percentage
            if percentage < 50:
                priority_level = 'low'
                priority_score = 100
            elif percentage < 75:
                priority_level = 'medium'
                priority_score = 75
            else:
                priority_level = 'high'
                priority_score = 50
            
            # Generate recommendations for low-scoring sub-categories
            for sub_cat, sub_score in sub_scores.items():
                if sub_cat in self.category_tips[category]['sub_categories']:
                    sub_info = self.category_tips[category]['sub_categories'][sub_cat]
                    
                    # Get appropriate tips based on performance level
                    tips = sub_info.get(priority_level, [])
                    
                    if tips:
                        recommendations.append({
                            'category': category,
                            'sub_category': sub_cat,
                            'title': f"Improve {sub_info['title']}",
                            'current_score': score,
                            'max_score': max_score,
                            'percentage': percentage,
                            'priority': priority_score,
                            'tips': tips[:3]  # Top 3 tips
                        })
        
        # Sort by priority (lowest scores first)
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        
        return recommendations[:top_n]
    
    def get_category_overview(self, category: str) -> Dict:
        """Get overview and description for a category"""
        if category in self.category_tips:
            info = self.category_tips[category]
            return {
                'title': info['title'],
                'description': info['description']
            }
        return {'title': category, 'description': 'No description available'}

