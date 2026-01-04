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
        title = Paragraph("AEO Score Auditor Report", self.styles['ReportTitle'])
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
        
        # Detailed page-by-page breakdown (for domain audits with detailed=True)
        if audit_type == 'domain' and detailed:
            page_results = audit_result.get('page_results', [])
            if page_results:
                story.append(PageBreak())
                detailed_heading = Paragraph("<b>Detailed Page-by-Page Analysis</b>", self.styles['ReportHeading'])
                story.append(detailed_heading)
                story.append(Spacer(1, 0.2*inch))
                
                info_text = Paragraph(
                    f"<i>This section contains detailed scoring breakdown for all {len(page_results)} audited pages.</i>",
                    self.styles['Normal']
                )
                story.append(info_text)
                story.append(Spacer(1, 0.3*inch))
                
                for idx, page_result in enumerate(page_results, 1):
                    # Page header
                    page_url = page_result.get('url', 'N/A')
                    page_score = page_result.get('overall_score', 0)
                    page_grade = page_result.get('grade', 'F')
                    
                    page_header = Paragraph(
                        f"<b>Page {idx}: {page_url}</b><br/>"
                        f"Score: {page_score}/100 | Grade: {page_grade}",
                        self.styles['ReportSubHeading']
                    )
                    story.append(page_header)
                    story.append(Spacer(1, 0.1*inch))
                    
                    # Page category breakdown
                    page_breakdown = page_result.get('breakdown', {})
                    if page_breakdown:
                        page_data = [['Category', 'Score', '%']]
                        for category, data in page_breakdown.items():
                            cat_name = category.replace('_', ' ').title()
                            score = data.get('score', 0)
                            max_score = data.get('max', 100)
                            percentage = data.get('percentage', 0)
                            page_data.append([
                                cat_name,
                                f"{score}/{max_score}",
                                f"{percentage:.1f}%"
                            ])
                        
                        page_table = Table(page_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
                        page_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9ca3af')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, -1), 8),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
                        ]))
                        story.append(page_table)
                        story.append(Spacer(1, 0.1*inch))
                        
                        # Sub-scores for each category (detailed view)
                        for category, data in page_breakdown.items():
                            sub_scores = data.get('sub_scores', {})
                            if sub_scores:
                                cat_name = category.replace('_', ' ').title()
                                sub_header = Paragraph(
                                    f"<i>{cat_name} Details:</i>",
                                    ParagraphStyle(name='SubDetail', parent=self.styles['Normal'], 
                                                 fontSize=8, textColor=colors.HexColor('#6b7280'))
                                )
                                story.append(sub_header)
                                
                                sub_data = []
                                for sub_cat, sub_score in sub_scores.items():
                                    sub_name = sub_cat.replace('_', ' ').title()
                                    sub_data.append([f"  • {sub_name}", str(sub_score)])
                                
                                if sub_data:
                                    sub_table = Table(sub_data, colWidths=[4*inch, 1*inch])
                                    sub_table.setStyle(TableStyle([
                                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                        ('FONTSIZE', (0, 0), (-1, -1), 7),
                                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4b5563')),
                                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                                        ('TOPPADDING', (0, 0), (-1, -1), 3),
                                    ]))
                                    story.append(sub_table)
                                    story.append(Spacer(1, 0.05*inch))
                        
                        # Generate page-specific recommendations
                        page_recommendations = self.rec_generator.generate_recommendations(page_result, top_n=3)
                        if page_recommendations:
                            rec_header = Paragraph(
                                "<b>💡 Top Improvement Suggestions:</b>",
                                ParagraphStyle(name='RecHeader', parent=self.styles['Normal'],
                                             fontSize=9, textColor=colors.HexColor('#059669'),
                                             fontName='Helvetica-Bold', spaceAfter=4)
                            )
                            story.append(Spacer(1, 0.1*inch))
                            story.append(rec_header)
                            
                            for rec in page_recommendations:
                                # Recommendation title
                                rec_title = Paragraph(
                                    f"<b>{rec['title']}</b> ({rec['percentage']:.0f}% complete)",
                                    ParagraphStyle(name='RecTitle', parent=self.styles['Normal'],
                                                 fontSize=8, textColor=colors.HexColor('#dc2626'),
                                                 fontName='Helvetica-Bold')
                                )
                                story.append(rec_title)
                                
                                # Recommendation tips (bullet list)
                                tips = rec.get('tips', [])
                                if tips:
                                    for tip in tips:
                                        tip_para = Paragraph(
                                            f"  • {tip}",
                                            ParagraphStyle(name='RecTip', parent=self.styles['Normal'],
                                                         fontSize=7, textColor=colors.HexColor('#374151'),
                                                         leftIndent=10, spaceAfter=2)
                                        )
                                        story.append(tip_para)
                                
                                story.append(Spacer(1, 0.08*inch))
                    
                    story.append(Spacer(1, 0.2*inch))
                    
                    # Add page break every 3 pages for readability
                    if idx % 3 == 0 and idx < len(page_results):
                        story.append(PageBreak())
        
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
            f"<i>Report generated by AEO Score Auditor | "
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


def generate_pdf_report(audit_result: Dict[str, Any], audit_type: str = 'page', detailed: bool = False) -> BytesIO:
    """Convenience function to generate PDF report"""
    generator = PDFReportGenerator()
    return generator.generate_report(audit_result, audit_type, detailed)

