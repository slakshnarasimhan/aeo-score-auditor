"""
PDF Report Generator for AEO Audit Results
"""
from io import BytesIO
from datetime import datetime
from typing import Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, ListFlowable, ListItem
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from loguru import logger
from reporting.recommendation_generator import RecommendationGenerator


class PDFReportGenerator:
    """Generates PDF reports from audit results"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.rec_generator = RecommendationGenerator()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Check if style already exists to avoid conflicts
        if 'ReportTitle' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='ReportTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#667eea'),
                spaceAfter=30,
                alignment=TA_CENTER
            ))
        
        # Check and add styles only if they don't exist
        if 'ReportHeading' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='ReportHeading',
                parent=self.styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#667eea'),
                spaceAfter=12,
                spaceBefore=12
            ))
        
        if 'ReportSubHeading' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='ReportSubHeading',
                parent=self.styles['Heading3'],
                fontSize=14,
                textColor=colors.HexColor('#555'),
                spaceAfter=8,
                spaceBefore=8
            ))
        
        if 'ReportScore' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='ReportScore',
                parent=self.styles['Normal'],
                fontSize=32,
                textColor=colors.HexColor('#667eea'),
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ))
    
    def generate_report(self, audit_result: Dict[str, Any], audit_type: str = 'page', detailed: bool = False) -> BytesIO:
        """
        Generate PDF report from audit results
        
        Args:
            audit_result: Complete audit result dictionary
            audit_type: 'page' or 'domain'
            detailed: If True, includes all page details and subsection breakdowns
            
        Returns:
            BytesIO buffer with PDF content
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=72)
        
        story = []
        
        # Title
        title = Paragraph("AEO/GEO Score Auditor Report", self.styles['ReportTitle'])
        story.append(title)
        story.append(Spacer(1, 0.2*inch))
        
        # Date and URL
        current_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        date_text = Paragraph(f"Generated: {current_date}", self.styles['Normal'])
        story.append(date_text)
        story.append(Spacer(1, 0.1*inch))
        
        if audit_type == 'page':
            url = audit_result.get('url', 'N/A')
        else:
            url = audit_result.get('domain', 'N/A')
        
        url_text = Paragraph(f"<b>URL:</b> {url}", self.styles['Normal'])
        story.append(url_text)
        story.append(Spacer(1, 0.3*inch))
        
        # Overall Score
        overall_score = audit_result.get('overall_score', 0)
        grade = audit_result.get('grade', 'F')
        
        score_text = Paragraph(f"<b>Overall AEO Score</b>", self.styles['ReportHeading'])
        story.append(score_text)
        story.append(Spacer(1, 0.1*inch))
        
        score_value = Paragraph(f"{overall_score}/100", self.styles['ReportScore'])
        story.append(score_value)
        
        grade_text = Paragraph(f"<b>Grade: {grade}</b>", self.styles['ReportHeading'])
        story.append(grade_text)
        story.append(Spacer(1, 0.3*inch))
        
        # Domain audit specific info
        if audit_type == 'domain':
            pages_audited = audit_result.get('pages_audited', 0)
            pages_successful = audit_result.get('pages_successful', 0)
            
            domain_info = [
                ['Pages Audited', f"{pages_successful}/{pages_audited}"],
                ['Domain', audit_result.get('domain', 'N/A')]
            ]
            
            domain_table = Table(domain_info, colWidths=[3*inch, 3*inch])
            domain_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            story.append(domain_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Score Breakdown
        breakdown_heading = Paragraph("<b>Score Breakdown by Category</b>", self.styles['ReportHeading'])
        story.append(breakdown_heading)
        story.append(Spacer(1, 0.2*inch))
        
        breakdown = audit_result.get('breakdown', {})
        breakdown_data = [['Category', 'Score', 'Percentage']]
        
        for category, data in breakdown.items():
            category_name = category.replace('_', ' ').title()
            score = data.get('score', 0)
            max_score = data.get('max', 100)
            percentage = data.get('percentage', 0)
            
            breakdown_data.append([
                category_name,
                f"{score}/{max_score}",
                f"{percentage:.1f}%"
            ])
        
        breakdown_table = Table(breakdown_data, colWidths=[3*inch, 2*inch, 2*inch])
        breakdown_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        story.append(breakdown_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Detailed Breakdown
        detailed_heading = Paragraph("<b>Detailed Category Analysis</b>", self.styles['ReportHeading'])
        story.append(detailed_heading)
        story.append(Spacer(1, 0.2*inch))
        
        for category, data in breakdown.items():
            category_name = category.replace('_', ' ').title()
            score = data.get('score', 0)
            max_score = data.get('max', 100)
            percentage = data.get('percentage', 0)
            
            # Category header
            cat_header = Paragraph(f"<b>{category_name}</b> - {score}/{max_score} ({percentage:.1f}%)", 
                                 self.styles['ReportSubHeading'])
            story.append(cat_header)
            
            # Sub-scores
            sub_scores = data.get('sub_scores', {})
            if sub_scores:
                sub_data = [['Metric', 'Score']]
                for sub_cat, sub_score in sub_scores.items():
                    sub_name = sub_cat.replace('_', ' ').title()
                    sub_data.append([sub_name, str(sub_score)])
                
                sub_table = Table(sub_data, colWidths=[4*inch, 2*inch])
                sub_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0e0e0')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
                ]))
                story.append(sub_table)
            
            story.append(Spacer(1, 0.2*inch))
        
        # Action Plan - Grouped by Issue Type (for domain audits with detailed=True)
        if audit_type == 'domain' and detailed:
            page_results = audit_result.get('page_results', [])
            if page_results:
                story.append(PageBreak())
                action_heading = Paragraph("<b>📋 Action Plan - Grouped by Issue Type</b>", self.styles['ReportHeading'])
                story.append(action_heading)
                story.append(Spacer(1, 0.1*inch))
                
                intro_text = Paragraph(
                    f"<i>Rather than fixing pages one by one, tackle issues that affect multiple pages together. "
                    f"This analysis covers all {len(page_results)} audited pages.</i>",
                    self.styles['Normal']
                )
                story.append(intro_text)
                story.append(Spacer(1, 0.2*inch))
                
                # Group pages by issues
                issue_groups = self._group_pages_by_issues(page_results)
                
                if not issue_groups:
                    no_issues_text = Paragraph(
                        "<i>Great! No major issues detected across your pages.</i>",
                        self.styles['Normal']
                    )
                    story.append(no_issues_text)
                else:
                    # Display grouped recommendations
                    for issue_type, issue_data in sorted(issue_groups.items(), key=lambda x: len(x[1]['pages']), reverse=True):
                        if not issue_data['pages']:
                            continue
                        
                        affected_count = len(issue_data['pages'])
                        
                        # Issue heading with count
                        issue_heading = Paragraph(
                            f"<b>{issue_data['icon']} {issue_type}</b>",
                            self.styles['ReportSubHeading']
                        )
                        story.append(issue_heading)
                        
                        affected_para = Paragraph(
                            f"<font color='#dc2626'><b>{affected_count} page(s) affected</b></font>",
                            self.styles['Normal']
                        )
                        story.append(affected_para)
                        story.append(Spacer(1, 0.08*inch))
                        
                        # Description and impact
                        desc_text = Paragraph(
                            f"<b>Why it matters:</b> {issue_data['description']}",
                            self.styles['Normal']
                        )
                        story.append(desc_text)
                        story.append(Spacer(1, 0.05*inch))
                        
                        impact_text = Paragraph(
                            f"<b>Potential impact:</b> {issue_data['impact']}",
                            self.styles['Normal']
                        )
                        story.append(impact_text)
                        story.append(Spacer(1, 0.08*inch))
                        
                        # How to fix
                        fix_text = Paragraph(
                            f"<b>How to fix:</b> {issue_data['fix']}",
                            ParagraphStyle(name='FixText', parent=self.styles['Normal'],
                                         textColor=colors.HexColor('#059669'))
                        )
                        story.append(fix_text)
                        story.append(Spacer(1, 0.08*inch))
                        
                        # Affected pages
                        pages_heading = Paragraph(
                            f"<b>Affected pages:</b>",
                            self.styles['Normal']
                        )
                        story.append(pages_heading)
                        story.append(Spacer(1, 0.05*inch))
                        
                        # Create bullet list of affected pages (show first 10, mention total)
                        display_pages = issue_data['pages'][:10]
                        for page_url in display_pages:
                            page_item = Paragraph(
                                f"• {self._truncate_url(page_url, 80)}",
                                ParagraphStyle(name='PageItem', parent=self.styles['Normal'],
                                             fontSize=8, leftIndent=10, textColor=colors.HexColor('#4b5563'))
                            )
                            story.append(page_item)
                        
                        if affected_count > 10:
                            more_pages = Paragraph(
                                f"<i>...and {affected_count - 10} more page(s)</i>",
                                ParagraphStyle(name='MorePages', parent=self.styles['Normal'],
                                             fontSize=8, leftIndent=10, textColor=colors.HexColor('#6b7280'))
                            )
                            story.append(more_pages)
                        
                        story.append(Spacer(1, 0.25*inch))
        
        # Recommendations (if available)
        # Generate detailed recommendations using our recommendation engine
        detailed_recommendations = self.rec_generator.generate_recommendations(audit_result, top_n=10)
        
        # Fallback to simple recommendations if detailed ones aren't available
        if not detailed_recommendations:
            detailed_recommendations = audit_result.get('recommendations', [])
        
        if detailed_recommendations:
            story.append(PageBreak())
            rec_heading = Paragraph("<b>💡 Prioritized Improvement Recommendations</b>", self.styles['ReportHeading'])
            story.append(rec_heading)
            story.append(Spacer(1, 0.1*inch))
            
            intro_text = Paragraph(
                "<i>Based on your audit results, here are the top recommendations to improve your AEO score, "
                "prioritized by potential impact:</i>",
                self.styles['Normal']
            )
            story.append(intro_text)
            story.append(Spacer(1, 0.2*inch))
            
            for i, rec in enumerate(detailed_recommendations[:10], 1):
                # Check if this is a detailed recommendation with tips
                if 'tips' in rec:
                    rec_title = rec.get('title', 'Improvement')
                    percentage = rec.get('percentage', 0)
                    current = rec.get('current_score', 0)
                    max_s = rec.get('max_score', 100)
                    
                    # Recommendation header
                    rec_header = f"<b>{i}. {rec_title}</b><br/>"
                    rec_header += f"<font color='#dc2626'>Current: {current}/{max_s} ({percentage:.0f}% complete)</font>"
                    
                    rec_para = Paragraph(rec_header, self.styles['Normal'])
                    story.append(rec_para)
                    story.append(Spacer(1, 0.05*inch))
                    
                    # Action items
                    tips = rec.get('tips', [])
                    if tips:
                        action_label = Paragraph(
                            "<b>Action Items:</b>",
                            ParagraphStyle(name='ActionLabel', parent=self.styles['Normal'],
                                         fontSize=9, textColor=colors.HexColor('#059669'))
                        )
                        story.append(action_label)
                        
                        for tip in tips:
                            tip_para = Paragraph(
                                f"  • {tip}",
                                ParagraphStyle(name='TipItem', parent=self.styles['Normal'],
                                             fontSize=9, leftIndent=15, spaceAfter=3)
                            )
                            story.append(tip_para)
                    
                    story.append(Spacer(1, 0.15*inch))
                else:
                    # Fallback to simple format
                    rec_title = rec.get('title', 'Improvement')
                    priority = rec.get('priority', 0)
                    current = rec.get('current_score', 0)
                    max_s = rec.get('max_score', 100)
                    potential = rec.get('potential_gain', 0)
                    
                    rec_text = f"<b>{i}. {rec_title}</b><br/>"
                    rec_text += f"Current: {current}/{max_s} | Potential Gain: {potential} points | Priority: {priority}%"
                    
                    rec_para = Paragraph(rec_text, self.styles['Normal'])
                    story.append(rec_para)
                    story.append(Spacer(1, 0.15*inch))
        
        # Domain-specific: Best/Worst pages
        if audit_type == 'domain':
            best_page = audit_result.get('best_page')
            worst_page = audit_result.get('worst_page')
            
            if best_page or worst_page:
                story.append(PageBreak())
                pages_heading = Paragraph("<b>Page Performance Summary</b>", self.styles['ReportHeading'])
                story.append(pages_heading)
                story.append(Spacer(1, 0.2*inch))
                
                if best_page:
                    best_text = Paragraph(
                        f"<b>🏆 Best Performing Page</b><br/>"
                        f"URL: {best_page.get('url', 'N/A')}<br/>"
                        f"Score: {best_page.get('overall_score', 0)}/100",
                        self.styles['Normal']
                    )
                    story.append(best_text)
                    story.append(Spacer(1, 0.2*inch))
                
                if worst_page:
                    worst_text = Paragraph(
                        f"<b>📉 Needs Most Improvement</b><br/>"
                        f"URL: {worst_page.get('url', 'N/A')}<br/>"
                        f"Score: {worst_page.get('overall_score', 0)}/100",
                        self.styles['Normal']
                    )
                    story.append(worst_text)
            
            # GEO Score Section (for domain audits only)
            geo_score = audit_result.get('geo_score')
            if geo_score:
                story.append(PageBreak())
                geo_heading = Paragraph(
                    "<b>🤖 GEO Score - Generative Engine Optimization</b>",
                    self.styles['ReportHeading']
                )
                story.append(geo_heading)
                story.append(Spacer(1, 0.2*inch))
                
                # GEO Score display
                geo_score_value = geo_score.get('geo_score', 0)
                geo_score_text = Paragraph(
                    f"<font size=36 color='#6366f1'><b>{geo_score_value}/100</b></font>",
                    self.styles['Normal']
                )
                story.append(geo_score_text)
                story.append(Spacer(1, 0.1*inch))
                
                # Summary
                summary_text = Paragraph(
                    f"<i>{geo_score.get('summary', '')}</i>",
                    self.styles['Normal']
                )
                story.append(summary_text)
                story.append(Spacer(1, 0.1*inch))
                
                # Brand info
                brand_info = Paragraph(
                    f"Brand: <b>{geo_score.get('brand_name', 'N/A')}</b> • "
                    f"{geo_score.get('pages_analyzed', 0)} pages analyzed",
                    self.styles['Normal']
                )
                story.append(brand_info)
                story.append(Spacer(1, 0.2*inch))
                
                # Component breakdown
                components_heading = Paragraph(
                    "<b>GEO Component Breakdown</b>",
                    self.styles['ReportSubHeading']
                )
                story.append(components_heading)
                story.append(Spacer(1, 0.1*inch))
                
                components = geo_score.get('components', {})
                geo_data = [['Component', 'Score', 'Max', '%']]
                
                for comp_name, comp_data in components.items():
                    display_name = comp_name.replace('_', ' ').title()
                    score = comp_data.get('score', 0)
                    max_score = comp_data.get('max', 0)
                    percentage = (score / max_score * 100) if max_score > 0 else 0
                    
                    geo_data.append([
                        display_name,
                        f"{score:.1f}",
                        str(max_score),
                        f"{percentage:.0f}%"
                    ])
                
                geo_table = Table(geo_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch])
                geo_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
                ]))
                story.append(geo_table)
                story.append(Spacer(1, 0.2*inch))
                
                # Recommended Actions
                actions = geo_score.get('recommended_actions', [])
                if actions:
                    actions_heading = Paragraph(
                        "<b>💡 Recommended Actions</b>",
                        self.styles['ReportSubHeading']
                    )
                    story.append(actions_heading)
                    story.append(Spacer(1, 0.1*inch))
                    
                    for action in actions:
                        action_item = Paragraph(
                            f"▸ {action}",
                            self.styles['Normal']
                        )
                        story.append(action_item)
                        story.append(Spacer(1, 0.05*inch))
                    
                    story.append(Spacer(1, 0.1*inch))
                
                # Disclaimer
                disclaimer = Paragraph(
                    "<i>Note: GEO Score estimates brand inclusion readiness for AI systems. "
                    "It does not predict rankings or guarantee citations.</i>",
                    self.styles['Normal']
                )
                story.append(disclaimer)
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        footer = Paragraph(
            f"<i>Report generated by AEO/GEO Score Auditor | "
            f"https://github.com/slakshnarasimhan/aeo-score-auditor</i>",
            ParagraphStyle(name='Footer', parent=self.styles['Normal'],
                          fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
        )
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        logger.info(f"Generated PDF report for {audit_type} audit")
        return buffer


    def _group_pages_by_issues(self, page_results: list) -> dict:
        """Group pages by the issues they need fixing"""
        issues = {
            'Missing Organization Schema': {
                'pages': [],
                'icon': '🏢',
                'description': 'Organization schema helps AI systems understand your brand identity and structure.',
                'impact': 'Improves brand recognition in AI responses',
                'fix': 'Add Organization schema markup to these pages with name, logo, and contact information.'
            },
            'No Author Information': {
                'pages': [],
                'icon': '✍️',
                'description': 'Author attribution builds trust and credibility for content.',
                'impact': 'Increases content trustworthiness for AI systems',
                'fix': 'Add author bylines and consider adding Person schema for key authors.'
            },
            'Missing Publication Dates': {
                'pages': [],
                'icon': '📅',
                'description': 'Dates help AI systems assess content freshness and relevance.',
                'impact': 'Better temporal context for AI inclusion',
                'fix': 'Add publication and last-modified dates to all content pages.'
            },
            'Low Answerability Score': {
                'pages': [],
                'icon': '❓',
                'description': 'Content doesn\'t effectively answer questions or provide clear information.',
                'impact': 'Reduces likelihood of being cited for Q&A prompts',
                'fix': 'Add Q&A sections, use question-format headings (H2), and provide direct answers.'
            },
            'Weak Structured Data': {
                'pages': [],
                'icon': '📊',
                'description': 'Missing or incomplete schema.org markup limits machine readability.',
                'impact': 'Harder for AI to extract structured information',
                'fix': 'Implement appropriate schema types (Article, Event, Place, Product, etc.) with rich properties.'
            },
            'Thin Content': {
                'pages': [],
                'icon': '📝',
                'description': 'Content lacks depth or comprehensive coverage.',
                'impact': 'Lower authority and usefulness signals',
                'fix': 'Expand content to 500+ words with detailed information, examples, and context.'
            },
            'Low Authority Signals': {
                'pages': [],
                'icon': '⭐',
                'description': 'Lacking trust signals like citations, sources, or expert attribution.',
                'impact': 'Reduces AI confidence in citing your content',
                'fix': 'Add external references, data sources, expert quotes, and clear attribution.'
            },
            'Poor Technical Performance': {
                'pages': [],
                'icon': '⚡',
                'description': 'Slow load times or technical issues impact user and AI crawler experience.',
                'impact': 'May limit crawlability and indexing',
                'fix': 'Optimize images, enable caching, use CDN, and reduce server response time.'
            }
        }
        
        for page in page_results:
            url = page.get('url', '')
            breakdown = page.get('breakdown', {})
            extracted_data = page.get('extracted_data', {})
            
            # Check for organization schema
            structured_data = breakdown.get('structured_data', {})
            if structured_data.get('score', 0) < structured_data.get('max', 15) * 0.3:
                issues['Weak Structured Data']['pages'].append(url)
            
            # Check for author
            if not extracted_data.get('has_author', False):
                issues['No Author Information']['pages'].append(url)
            
            # Check for dates
            if not extracted_data.get('has_dates', False):
                issues['Missing Publication Dates']['pages'].append(url)
            
            # Check answerability
            answerability = breakdown.get('answerability', {})
            if answerability.get('score', 0) < answerability.get('max', 30) * 0.5:
                issues['Low Answerability Score']['pages'].append(url)
            
            # Check content quality (word count)
            word_count = extracted_data.get('word_count', 0)
            if word_count < 300:
                issues['Thin Content']['pages'].append(url)
            
            # Check authority
            authority = breakdown.get('authority', {})
            if authority.get('score', 0) < authority.get('max', 18) * 0.3:
                issues['Low Authority Signals']['pages'].append(url)
            
            # Check technical
            technical = breakdown.get('technical', {})
            if technical.get('score', 0) < technical.get('max', 10) * 0.6:
                issues['Poor Technical Performance']['pages'].append(url)
        
        # Remove issues with no affected pages
        return {k: v for k, v in issues.items() if v['pages']}
    
    def _truncate_url(self, url: str, max_len: int = 60) -> str:
        """Truncate URL for display"""
        if len(url) <= max_len:
            return url
        return url[:max_len-3] + '...'


def generate_pdf_report(audit_result: Dict[str, Any], audit_type: str = 'page', detailed: bool = False) -> BytesIO:
    """Convenience function to generate PDF report"""
    generator = PDFReportGenerator()
    return generator.generate_report(audit_result, audit_type, detailed)

