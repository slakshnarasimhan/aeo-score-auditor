"""
Chapter-book PDF Report Generator for AEO Audit Results.
Mirrors the frontend ReportBook layout: Cover → Summary → Categories → GEO → Actions.
"""
from io import BytesIO
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import Flowable
from loguru import logger

from reporting.report_utils import (
    CATEGORY_ACTIONS,
    format_category_name,
    get_category_description,
    get_score_label,
    grade_color_hex,
    score_color_hex,
)
from reporting.recommendation_generator import RecommendationGenerator

# Palette aligned with frontend report book
INDIGO = HexColor("#4f46e5")
INDIGO_LIGHT = HexColor("#a5b4fc")
VIOLET = HexColor("#7c3aed")
STONE_900 = HexColor("#1c1917")
STONE_600 = HexColor("#57534e")
STONE_400 = HexColor("#a8a29e")
PAPER = HexColor("#faf9f7")
EMERALD = HexColor("#10b981")
ROSE = HexColor("#f43f5e")


class ProgressBar(Flowable):
    """Horizontal score progress bar."""

    def __init__(self, percentage: float, width: float = 4.5 * inch, height: float = 10):
        super().__init__()
        self.percentage = max(0, min(100, percentage))
        self.width = width
        self.height = height

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        canvas.setFillColor(HexColor("#e7e5e4"))
        canvas.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)
        fill_width = self.width * (self.percentage / 100)
        if fill_width > 0:
            canvas.setFillColor(HexColor(score_color_hex(self.percentage)))
            canvas.roundRect(0, 0, fill_width, self.height, 4, fill=1, stroke=0)


class ChapterMarker(Flowable):
    """Invisible marker that sets the current chapter number for page headers."""

    def __init__(self, chapter_num: int):
        super().__init__()
        self.chapter_num = chapter_num

    def wrap(self, availWidth, availHeight):
        return 0, 0

    def draw(self):
        self.canv._doctemplate.chapter_num = self.chapter_num


class ChapterBookDoc(BaseDocTemplate):
    """Document with chapter accent bar and page counter."""

    def __init__(self, buffer, total_chapters: int, **kwargs):
        self.total_chapters = total_chapters
        self.chapter_num = 1
        BaseDocTemplate.__init__(self, buffer, **kwargs)


class PDFReportGenerator:
    """Generates chapter-book PDF reports from audit results."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.rec_generator = RecommendationGenerator()

    def _setup_custom_styles(self):
        custom = {
            "ChapterKicker": dict(
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=INDIGO,
                spaceAfter=4,
                fontName="Helvetica-Bold",
            ),
            "ChapterTitle": dict(
                parent=self.styles["Heading1"],
                fontSize=22,
                textColor=STONE_900,
                spaceAfter=14,
                fontName="Helvetica-Bold",
            ),
            "ChapterSubtitle": dict(
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=STONE_600,
                spaceAfter=10,
            ),
            "BodyText": dict(
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=STONE_900,
                leading=14,
            ),
            "InsightBullet": dict(
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=STONE_600,
                leftIndent=14,
                spaceAfter=6,
                bulletIndent=0,
            ),
            "SectionLabel": dict(
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=STONE_400,
                spaceAfter=6,
                fontName="Helvetica-Bold",
            ),
            "CoverKicker": dict(
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=INDIGO,
                alignment=TA_CENTER,
                spaceAfter=8,
                fontName="Helvetica-Bold",
            ),
            "CoverTitle": dict(
                parent=self.styles["Heading1"],
                fontSize=20,
                textColor=STONE_900,
                alignment=TA_CENTER,
                spaceAfter=6,
                fontName="Helvetica-Bold",
            ),
            "CoverScore": dict(
                parent=self.styles["Normal"],
                fontSize=42,
                textColor=STONE_900,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
                spaceAfter=4,
            ),
            "CoverGrade": dict(
                parent=self.styles["Normal"],
                fontSize=36,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
                spaceAfter=6,
            ),
            "Footer": dict(
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=STONE_400,
                alignment=TA_CENTER,
            ),
        }
        for name, kwargs in custom.items():
            if name not in self.styles.byName:
                self.styles.add(ParagraphStyle(name=name, **kwargs))

    def _chapter_page_decorator(self, canvas, doc):
        canvas.saveState()
        page_w, page_h = letter
        canvas.setFillColor(INDIGO_LIGHT)
        canvas.rect(0.55 * inch, 0.55 * inch, 0.06 * inch, page_h - 1.1 * inch, fill=1, stroke=0)
        canvas.setFillColor(PAPER)
        canvas.rect(0.75 * inch, 0.55 * inch, page_w - 1.35 * inch, page_h - 1.1 * inch, fill=1, stroke=0)
        chapter = min(getattr(doc, "chapter_num", 1), doc.total_chapters)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(STONE_400)
        canvas.drawRightString(page_w - 0.75 * inch, page_h - 0.65 * inch, f"{chapter} / {doc.total_chapters}")
        canvas.restoreState()

    def _build_chapters(self, audit_result: Dict[str, Any], audit_type: str) -> List[Dict[str, Any]]:
        chapters: List[Dict[str, Any]] = [
            {"type": "cover"},
            {"type": "summary"},
        ]
        for category in audit_result.get("breakdown", {}):
            chapters.append({"type": "category", "category": category})
        if audit_type == "domain" and audit_result.get("geo_score"):
            chapters.append({"type": "geo"})
        chapters.append({"type": "actions"})
        return chapters

    def generate_report(
        self, audit_result: Dict[str, Any], audit_type: str = "page", detailed: bool = False
    ) -> BytesIO:
        buffer = BytesIO()
        chapters = self._build_chapters(audit_result, audit_type)

        doc = ChapterBookDoc(
            buffer,
            total_chapters=len(chapters),
            pagesize=letter,
            rightMargin=0.85 * inch,
            leftMargin=0.85 * inch,
            topMargin=0.85 * inch,
            bottomMargin=0.75 * inch,
        )

        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id="chapter_frame",
        )
        template = PageTemplate(id="chapter", frames=[frame], onPage=self._chapter_page_decorator)
        doc.addPageTemplates([template])

        story: List[Any] = []
        for i, chapter in enumerate(chapters):
            if i > 0:
                story.append(PageBreak())
            story.append(ChapterMarker(i + 1))
            self._render_chapter(story, chapter, audit_result, audit_type, detailed, i + 1)

        story.append(Spacer(1, 0.3 * inch))
        story.append(
            Paragraph(
                "<i>AEO/GEO Score Auditor — Chapter Book Report</i>",
                self.styles["Footer"],
            )
        )

        doc.build(story)
        buffer.seek(0)
        logger.info(f"Generated chapter-book PDF for {audit_type} audit ({len(chapters)} chapters)")
        return buffer

    def _render_chapter(
        self,
        story: List[Any],
        chapter: Dict[str, Any],
        audit_result: Dict[str, Any],
        audit_type: str,
        detailed: bool,
        chapter_index: int,
    ):
        ctype = chapter["type"]
        if ctype == "cover":
            self._add_cover(story, audit_result, audit_type)
        elif ctype == "summary":
            self._add_summary(story, audit_result, audit_type)
        elif ctype == "category":
            self._add_category(story, chapter["category"], audit_result, detailed, chapter_index - 2)
        elif ctype == "geo":
            self._add_geo(story, audit_result)
        elif ctype == "actions":
            self._add_actions(story, audit_result, audit_type, detailed)

    def _add_cover(self, story: List[Any], audit_result: Dict[str, Any], audit_type: str):
        story.append(Spacer(1, 0.4 * inch))
        story.append(Paragraph("AEO / GEO AUDIT REPORT", self.styles["CoverKicker"]))

        if audit_type == "domain":
            title = audit_result.get("domain", "N/A")
            subtitle = (
                f"{audit_result.get('pages_successful', 0)} of "
                f"{audit_result.get('pages_audited', 0)} pages audited"
            )
        else:
            title = audit_result.get("url", "N/A")
            subtitle = "Single Page Audit"

        story.append(Paragraph(title, self.styles["CoverTitle"]))
        story.append(Paragraph(subtitle, ParagraphStyle(
            name="CoverSub", parent=self.styles["Normal"], alignment=TA_CENTER,
            textColor=STONE_600, fontSize=10, spaceAfter=20,
        )))

        score = audit_result.get("overall_score", 0)
        grade = audit_result.get("grade", "F")
        story.append(Paragraph(f"{score}", self.styles["CoverScore"]))
        story.append(Paragraph(
            f'<font color="#a8a29e">/ 100</font>',
            ParagraphStyle(name="CoverMax", parent=self.styles["Normal"], alignment=TA_CENTER, fontSize=14),
        ))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(
            f'<font color="{grade_color_hex(grade)}">{grade}</font>',
            self.styles["CoverGrade"],
        ))
        story.append(Paragraph(
            f'{get_score_label(score)} &nbsp;·&nbsp; {datetime.now().strftime("%B %d, %Y")}',
            ParagraphStyle(name="CoverMeta", parent=self.styles["Normal"], alignment=TA_CENTER,
                           textColor=STONE_600, fontSize=10),
        ))

        classification = audit_result.get("content_classification")
        if classification:
            story.append(Spacer(1, 0.25 * inch))
            ctype = classification.get("type", "").upper()
            conf = classification.get("confidence", "")
            desc = classification.get("description", "")
            story.append(Paragraph(
                f'<b>Content Type:</b> {ctype} ({conf} confidence)<br/>'
                f'<font color="#57534e"><i>{desc}</i></font>',
                ParagraphStyle(name="ContentType", parent=self.styles["Normal"], fontSize=9,
                               backColor=HexColor("#f5f5f4"), borderPadding=8),
            ))

    def _add_summary(self, story: List[Any], audit_result: Dict[str, Any], audit_type: str):
        story.append(Paragraph("CHAPTER OVERVIEW", self.styles["ChapterKicker"]))
        story.append(Paragraph("Executive Summary", self.styles["ChapterTitle"]))

        breakdown = audit_result.get("breakdown", {})
        sorted_cats = sorted(
            breakdown.items(),
            key=lambda x: x[1].get("percentage", 0),
            reverse=True,
        )
        score = audit_result.get("overall_score", 0)
        insights = [f"Overall performance is {get_score_label(score).lower()} at {score}/100."]
        if sorted_cats:
            strongest = sorted_cats[0]
            weakest = sorted_cats[-1]
            insights.append(
                f"Strongest area: {format_category_name(strongest[0])} "
                f"({strongest[1].get('percentage', 0):.0f}%)."
            )
            if strongest[0] != weakest[0]:
                insights.append(
                    f"Priority focus: {format_category_name(weakest[0])} "
                    f"({weakest[1].get('percentage', 0):.0f}%)."
                )

        if audit_type == "domain":
            best = audit_result.get("best_page")
            worst = audit_result.get("worst_page")
            if best and worst:
                insights.append(
                    f"Best page scores {best.get('overall_score', 0)}/100; "
                    f"weakest page scores {worst.get('overall_score', 0)}/100."
                )

        for insight in insights:
            story.append(Paragraph(f"• {insight}", self.styles["InsightBullet"]))

        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("CATEGORY SNAPSHOT", self.styles["SectionLabel"]))
        for category, data in sorted_cats:
            pct = data.get("percentage", 0)
            story.append(Paragraph(
                f'<b>{format_category_name(category)}</b> — '
                f'<font color="{score_color_hex(pct)}">{pct:.0f}%</font>',
                self.styles["BodyText"],
            ))
            story.append(ProgressBar(pct))
            story.append(Spacer(1, 0.08 * inch))

        if audit_type == "domain":
            best = audit_result.get("best_page")
            worst = audit_result.get("worst_page")
            if best and worst:
                story.append(Spacer(1, 0.15 * inch))
                page_data = [
                    [
                        Paragraph("<b>BEST PAGE</b>", ParagraphStyle(name="BestL", fontSize=8, textColor=EMERALD)),
                        Paragraph("<b>NEEDS IMPROVEMENT</b>", ParagraphStyle(name="WorstL", fontSize=8, textColor=ROSE)),
                    ],
                    [
                        Paragraph(f"<b>{best.get('overall_score', 0)}/100</b>", self.styles["BodyText"]),
                        Paragraph(f"<b>{worst.get('overall_score', 0)}/100</b>", self.styles["BodyText"]),
                    ],
                    [
                        Paragraph(best.get("url", ""), ParagraphStyle(name="BestU", fontSize=8, textColor=STONE_600)),
                        Paragraph(worst.get("url", ""), ParagraphStyle(name="WorstU", fontSize=8, textColor=STONE_600)),
                    ],
                ]
                t = Table(page_data, colWidths=[3.25 * inch, 3.25 * inch])
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (0, -1), HexColor("#ecfdf5")),
                    ("BACKGROUND", (1, 0), (1, -1), HexColor("#fff1f2")),
                    ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#e7e5e4")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#e7e5e4")),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ]))
                story.append(t)

    def _add_category(
        self,
        story: List[Any],
        category: str,
        audit_result: Dict[str, Any],
        detailed: bool,
        cat_index: int,
    ):
        data = audit_result.get("breakdown", {}).get(category, {})
        pct = data.get("percentage", 0)
        score = data.get("score", 0)
        max_score = data.get("max", 100)

        story.append(Paragraph(f"CATEGORY {cat_index}", self.styles["ChapterKicker"]))
        story.append(Paragraph(format_category_name(category), self.styles["ChapterTitle"]))
        story.append(Paragraph(get_category_description(category), self.styles["ChapterSubtitle"]))
        story.append(Paragraph(
            f'<font color="{score_color_hex(pct)}"><b>{score}</b></font>'
            f'<font color="#a8a29e">/{max_score}</font>'
            f' &nbsp;&nbsp; <font color="{score_color_hex(pct)}"><b>{pct:.1f}%</b></font>',
            ParagraphStyle(name="CatScore", parent=self.styles["BodyText"], fontSize=16, spaceAfter=6),
        ))
        story.append(ProgressBar(pct))
        story.append(Spacer(1, 0.2 * inch))

        sub_scores = data.get("sub_scores", {})
        if sub_scores:
            story.append(Paragraph("SUB-SCORES", self.styles["SectionLabel"]))
            rows = [["Metric", "Score"]]
            for sub, val in sub_scores.items():
                rows.append([format_category_name(sub), str(val)])
            t = Table(rows, colWidths=[4 * inch, 1.5 * inch])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f5f5f4")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#e7e5e4")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#e7e5e4")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.15 * inch))

        best = data.get("best_page")
        worst = data.get("worst_page")
        if best and worst:
            story.append(Paragraph(
                f'<font color="#10b981"><b>Best:</b></font> {best.get("score", 0):.1f} — {self._truncate_url(best.get("url", ""))}<br/>'
                f'<font color="#f43f5e"><b>Worst:</b></font> {worst.get("score", 0):.1f} — {self._truncate_url(worst.get("url", ""))}',
                ParagraphStyle(name="BestWorst", parent=self.styles["BodyText"], fontSize=9),
            ))
            story.append(Spacer(1, 0.15 * inch))

        page_scores = data.get("page_scores", [])
        if page_scores and detailed:
            story.append(Paragraph("PER-PAGE BREAKDOWN", self.styles["SectionLabel"]))
            rows = [["Page URL", "Score", "%"]]
            for page in sorted(page_scores, key=lambda p: p.get("score", 0), reverse=True):
                rows.append([
                    self._truncate_url(page.get("url", ""), 70),
                    f"{page.get('score', 0):.1f}/{max_score}",
                    f"{page.get('percentage', 0):.0f}%",
                ])
            t = Table(rows, colWidths=[3.8 * inch, 1.2 * inch, 0.8 * inch])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#eef2ff")),
                ("TEXTCOLOR", (0, 0), (-1, 0), INDIGO),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#e7e5e4")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#e7e5e4")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(t)

    def _add_geo(self, story: List[Any], audit_result: Dict[str, Any]):
        geo = audit_result.get("geo_score", {})
        story.append(Paragraph("GENERATIVE ENGINE OPTIMIZATION", self.styles["ChapterKicker"]))
        story.append(Paragraph("GEO Score", self.styles["ChapterTitle"]))
        story.append(Paragraph(
            f"Brand inclusion readiness — {geo.get('brand_name', 'N/A')} "
            f"across {geo.get('pages_analyzed', 0)} pages",
            self.styles["ChapterSubtitle"],
        ))

        geo_score = geo.get("geo_score", 0)
        story.append(Paragraph(
            f'<font color="#7c3aed"><b>{geo_score}</b></font><font color="#a8a29e">/100</font>',
            ParagraphStyle(name="GeoScore", parent=self.styles["BodyText"], fontSize=28, spaceAfter=8),
        ))
        story.append(Paragraph(f'<i>{geo.get("summary", "")}</i>', self.styles["BodyText"]))
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("COMPONENTS", self.styles["SectionLabel"]))
        rows = [["Component", "Score", "%"]]
        for name, comp in geo.get("components", {}).items():
            s, m = comp.get("score", 0), comp.get("max", 1)
            pct = (s / m * 100) if m else 0
            rows.append([format_category_name(name), f"{s:.1f}/{m}", f"{pct:.0f}%"])
        t = Table(rows, colWidths=[3 * inch, 1.5 * inch, 1 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), VIOLET),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#e7e5e4")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#e7e5e4")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph(
            "<i>GEO Score estimates brand inclusion readiness for AI systems. "
            "It does not predict rankings or guarantee citations.</i>",
            ParagraphStyle(name="GeoNote", parent=self.styles["BodyText"], fontSize=8, textColor=VIOLET),
        ))

    def _add_actions(
        self,
        story: List[Any],
        audit_result: Dict[str, Any],
        audit_type: str,
        detailed: bool,
    ):
        story.append(Paragraph("NEXT STEPS", self.styles["ChapterKicker"]))
        story.append(Paragraph("Recommended Actions", self.styles["ChapterTitle"]))

        breakdown = audit_result.get("breakdown", {})
        weak = sorted(
            [(k, v) for k, v in breakdown.items() if v.get("percentage", 0) < 70],
            key=lambda x: x[1].get("percentage", 0),
        )
        geo = audit_result.get("geo_score") or {}
        geo_actions = geo.get("recommended_actions", [])

        if not weak and not geo_actions:
            story.append(Paragraph(
                "<b>Strong performance across the board.</b><br/>"
                "Maintain content freshness and monitor scores as you publish new pages.",
                ParagraphStyle(name="AllGood", parent=self.styles["BodyText"], backColor=HexColor("#ecfdf5"),
                               borderPadding=10),
            ))

        if geo_actions:
            story.append(Paragraph("GEO PRIORITIES", self.styles["SectionLabel"]))
            for i, action in enumerate(geo_actions, 1):
                story.append(Paragraph(f"<b>{i}.</b> {action}", self.styles["BodyText"]))
                story.append(Spacer(1, 0.06 * inch))

        if weak:
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph("AEO IMPROVEMENT AREAS", self.styles["SectionLabel"]))
            for category, data in weak:
                pct = data.get("percentage", 0)
                action = CATEGORY_ACTIONS.get(
                    category,
                    f"Review and improve {format_category_name(category).lower()} signals across audited pages.",
                )
                story.append(Paragraph(
                    f'<b>{format_category_name(category)}</b> '
                    f'<font color="#f43f5e">({pct:.0f}%)</font><br/>'
                    f'<font color="#57534e"><i>{get_category_description(category)}</i></font><br/>'
                    f'{action}',
                    ParagraphStyle(name="ActionCard", parent=self.styles["BodyText"], fontSize=9,
                                   backColor=HexColor("#fafaf9"), borderPadding=8, spaceAfter=10),
                ))

        if detailed and audit_type == "domain":
            page_results = audit_result.get("page_results", [])
            if page_results:
                story.append(PageBreak())
                story.append(Paragraph("DETAILED ACTION PLAN", self.styles["ChapterKicker"]))
                story.append(Paragraph("Issues Grouped by Type", self.styles["ChapterTitle"]))
                story.append(Paragraph(
                    f"<i>Issues affecting multiple pages across all {len(page_results)} audited pages.</i>",
                    self.styles["ChapterSubtitle"],
                ))
                issue_groups = self._group_pages_by_issues(page_results)
                for issue_type, issue_data in sorted(
                    issue_groups.items(), key=lambda x: len(x[1]["pages"]), reverse=True
                ):
                    if not issue_data["pages"]:
                        continue
                    count = len(issue_data["pages"])
                    story.append(Paragraph(
                        f'<b>{issue_data["icon"]} {issue_type}</b> — '
                        f'<font color="#dc2626">{count} page(s) affected</font>',
                        ParagraphStyle(name="IssueH", parent=self.styles["BodyText"], fontSize=11, spaceAfter=4),
                    ))
                    story.append(Paragraph(f'<b>Why:</b> {issue_data["description"]}', self.styles["BodyText"]))
                    story.append(Paragraph(f'<b>Fix:</b> <font color="#059669">{issue_data["fix"]}</font>',
                                           ParagraphStyle(name="Fix", parent=self.styles["BodyText"], fontSize=9)))
                    for url in issue_data["pages"][:8]:
                        story.append(Paragraph(
                            f"• {self._truncate_url(url, 75)}",
                            ParagraphStyle(name="AffPage", parent=self.styles["BodyText"], fontSize=8,
                                           leftIndent=10, textColor=STONE_600),
                        ))
                    if count > 8:
                        story.append(Paragraph(f"<i>...and {count - 8} more</i>",
                                               ParagraphStyle(name="More", fontSize=8, textColor=STONE_400)))
                    story.append(Spacer(1, 0.12 * inch))

    def _group_pages_by_issues(self, page_results: list) -> dict:
        """Group pages by the issues they need fixing."""
        issues = {
            "Missing Organization Schema": {
                "pages": [],
                "icon": "🏢",
                "description": "Organization schema helps AI systems understand your brand identity and structure.",
                "impact": "Improves brand recognition in AI responses",
                "fix": "Add Organization schema markup to these pages with name, logo, and contact information.",
            },
            "No Author Information": {
                "pages": [],
                "icon": "✍️",
                "description": "Author attribution builds trust and credibility for content.",
                "impact": "Increases content trustworthiness for AI systems",
                "fix": "Add author bylines and consider adding Person schema for key authors.",
            },
            "Missing Publication Dates": {
                "pages": [],
                "icon": "📅",
                "description": "Dates help AI systems assess content freshness and relevance.",
                "impact": "Better temporal context for AI inclusion",
                "fix": "Add publication and last-modified dates to all content pages.",
            },
            "Low Answerability Score": {
                "pages": [],
                "icon": "❓",
                "description": "Content doesn't effectively answer questions or provide clear information.",
                "impact": "Reduces likelihood of being cited for Q&A prompts",
                "fix": "Add Q&A sections, use question-format headings (H2), and provide direct answers.",
            },
            "Weak Structured Data": {
                "pages": [],
                "icon": "📊",
                "description": "Missing or incomplete schema.org markup limits machine readability.",
                "impact": "Harder for AI to extract structured information",
                "fix": "Implement appropriate schema types (Article, Event, Place, Product, etc.) with rich properties.",
            },
            "Thin Content": {
                "pages": [],
                "icon": "📝",
                "description": "Content lacks depth or comprehensive coverage.",
                "impact": "Lower authority and usefulness signals",
                "fix": "Expand content to 500+ words with detailed information, examples, and context.",
            },
            "Low Authority Signals": {
                "pages": [],
                "icon": "⭐",
                "description": "Lacking trust signals like citations, sources, or expert attribution.",
                "impact": "Reduces AI confidence in citing your content",
                "fix": "Add external references, data sources, expert quotes, and clear attribution.",
            },
            "Poor Technical Performance": {
                "pages": [],
                "icon": "⚡",
                "description": "Slow load times or technical issues impact user and AI crawler experience.",
                "impact": "May limit crawlability and indexing",
                "fix": "Optimize images, enable caching, use CDN, and reduce server response time.",
            },
        }

        for page in page_results:
            url = page.get("url", "")
            bd = page.get("breakdown", {})
            extracted = page.get("extracted_data", {})

            structured = bd.get("structured_data", {})
            if structured.get("score", 0) < structured.get("max", 15) * 0.3:
                issues["Weak Structured Data"]["pages"].append(url)
            if not extracted.get("has_author", False):
                issues["No Author Information"]["pages"].append(url)
            if not extracted.get("has_dates", False):
                issues["Missing Publication Dates"]["pages"].append(url)
            answerability = bd.get("answerability", {})
            if answerability.get("score", 0) < answerability.get("max", 30) * 0.5:
                issues["Low Answerability Score"]["pages"].append(url)
            if extracted.get("word_count", 0) < 300:
                issues["Thin Content"]["pages"].append(url)
            authority = bd.get("authority", {})
            if authority.get("score", 0) < authority.get("max", 18) * 0.3:
                issues["Low Authority Signals"]["pages"].append(url)
            technical = bd.get("technical", {})
            if technical.get("score", 0) < technical.get("max", 10) * 0.6:
                issues["Poor Technical Performance"]["pages"].append(url)

        return {k: v for k, v in issues.items() if v["pages"]}

    def _truncate_url(self, url: str, max_len: int = 60) -> str:
        if len(url) <= max_len:
            return url
        return url[: max_len - 3] + "..."


def generate_pdf_report(
    audit_result: Dict[str, Any], audit_type: str = "page", detailed: bool = False
) -> BytesIO:
    """Convenience function to generate chapter-book PDF report."""
    generator = PDFReportGenerator()
    return generator.generate_report(audit_result, audit_type, detailed)
