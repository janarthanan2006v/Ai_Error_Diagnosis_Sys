"""
PDF Report Generator using ReportLab.

Generates professional, structured PDF reports containing:
- Error screenshot
- Error summary
- Root cause and confidence score
- Recommended fix
- Step-by-step solution
- Prevention tips
- Related errors
"""
from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import KeepTogether

from app.core.logging import get_logger
from app.schemas.diagnosis import DiagnosisResult, VisionAnalysisResult

logger = get_logger(__name__)

# ── Colour Palette ────────────────────────────────────────────────────────────
DARK_BG = colors.HexColor("#1a1a2e")
ACCENT_BLUE = colors.HexColor("#0f3460")
ACCENT_CYAN = colors.HexColor("#16213e")
HIGHLIGHT = colors.HexColor("#e94560")
TEXT_LIGHT = colors.HexColor("#f0f0f0")
TEXT_DARK = colors.HexColor("#333333")
SUCCESS_GREEN = colors.HexColor("#27ae60")
WARNING_AMBER = colors.HexColor("#f39c12")
ERROR_RED = colors.HexColor("#e74c3c")
SECTION_BG = colors.HexColor("#f8f9fa")


class PDFGenerator:
    """
    Generates professional PDF reports for error diagnoses.
    """

    def __init__(self, reports_dir: Path) -> None:
        """
        Initialise the PDF generator.

        Args:
            reports_dir: Directory where generated PDF reports are saved.
        """
        self._reports_dir = reports_dir
        self._reports_dir.mkdir(parents=True, exist_ok=True)
        self._styles = self._build_styles()

    def generate(
        self,
        report_id: str,
        image_path: Path,
        vision_result: VisionAnalysisResult,
        diagnosis: DiagnosisResult,
    ) -> Path:
        """
        Generate and save a PDF report.

        Args:
            report_id: Unique identifier for this report.
            image_path: Path to the error screenshot.
            vision_result: Structured vision analysis output.
            diagnosis: Structured diagnosis output.

        Returns:
            Path to the generated PDF file.
        """
        pdf_path = self._reports_dir / f"{report_id}.pdf"

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        story = self._build_story(report_id, image_path, vision_result, diagnosis)
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)

        logger.info("PDF report generated: %s", pdf_path.name)
        return pdf_path

    # ── Story Builder ─────────────────────────────────────────────────────────

    def _build_story(
        self,
        report_id: str,
        image_path: Path,
        vision_result: VisionAnalysisResult,
        diagnosis: DiagnosisResult,
    ) -> list:
        """Build the complete ReportLab story (list of flowables)."""
        story = []

        # Title Header
        story.extend(self._build_title_section(report_id, vision_result))

        # Error Screenshot
        if image_path.exists():
            story.extend(self._build_screenshot_section(image_path))

        # Error Details Table
        story.extend(self._build_error_details_section(vision_result))

        # Confidence Banner
        story.extend(self._build_confidence_section(diagnosis.confidence_score))

        # Root Cause
        story.extend(self._build_section("🔍 Root Cause", diagnosis.root_cause))

        # Error Summary
        story.extend(self._build_section("📋 Error Summary", diagnosis.error_summary))

        # Recommended Fix
        story.extend(self._build_section("✅ Recommended Fix", diagnosis.recommended_fix))

        # Step-by-step Solution
        story.extend(
            self._build_list_section(
                "🛠️ Step-by-Step Solution",
                diagnosis.step_by_step_solution,
            )
        )

        # Prevention Tips
        story.extend(
            self._build_list_section(
                "🛡️ Prevention Tips",
                diagnosis.prevention_tips,
            )
        )

        # Related Errors
        if diagnosis.related_errors:
            story.extend(
                self._build_list_section(
                    "🔗 Related Errors",
                    diagnosis.related_errors,
                )
            )

        # Footer note
        story.append(Spacer(1, 10 * mm))
        story.append(
            Paragraph(
                f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                f"Report ID: {report_id}",
                self._styles["footer_note"],
            )
        )

        return story

    # ── Section Builders ──────────────────────────────────────────────────────

    def _build_title_section(self, report_id: str, vision: VisionAnalysisResult) -> list:
        items = []
        items.append(
            Paragraph("AI Error Diagnosis Report", self._styles["main_title"])
        )
        items.append(
            Paragraph(vision.error_title or "Error Analysis", self._styles["sub_title"])
        )
        items.append(
            Paragraph(
                f"Report ID: {report_id} &nbsp;|&nbsp; {datetime.now().strftime('%B %d, %Y')}",
                self._styles["meta_info"],
            )
        )
        items.append(HRFlowable(width="100%", thickness=2, color=HIGHLIGHT))
        items.append(Spacer(1, 6 * mm))
        return items

    def _build_screenshot_section(self, image_path: Path) -> list:
        items = []
        items.append(Paragraph("📸 Error Screenshot", self._styles["section_heading"]))
        items.append(Spacer(1, 3 * mm))
        try:
            img = Image(str(image_path), width=160 * mm, height=90 * mm, kind="proportional")
            items.append(img)
        except Exception as exc:
            logger.warning("Could not embed screenshot in PDF: %s", exc)
            items.append(
                Paragraph("[Screenshot could not be embedded]", self._styles["body_italic"])
            )
        items.append(Spacer(1, 6 * mm))
        return items

    def _build_error_details_section(self, vision: VisionAnalysisResult) -> list:
        items = []
        items.append(Paragraph("ℹ️ Error Details", self._styles["section_heading"]))
        items.append(Spacer(1, 3 * mm))

        table_data = [
            ["Field", "Value"],
            ["Language", vision.language],
            ["Framework", vision.framework],
            ["Environment", vision.environment],
            ["Error Message", vision.error_message[:200] + ("..." if len(vision.error_message) > 200 else "")],
        ]

        if vision.raw_stacktrace:
            table_data.append(
                ["Stack Trace", vision.raw_stacktrace[:300] + ("..." if len(vision.raw_stacktrace) > 300 else "")]
            )

        table = Table(
            table_data,
            colWidths=[40 * mm, 130 * mm],
            hAlign="LEFT",
        )
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), TEXT_LIGHT),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BACKGROUND", (0, 1), (0, -1), SECTION_BG),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SECTION_BG]),
                ("WORDWRAP", (0, 0), (-1, -1), True),
            ])
        )
        items.append(table)
        items.append(Spacer(1, 6 * mm))
        return items

    def _build_confidence_section(self, score: float) -> list:
        items = []
        percentage = int(score * 100)
        if score >= 0.8:
            color = SUCCESS_GREEN
            label = "HIGH"
        elif score >= 0.5:
            color = WARNING_AMBER
            label = "MEDIUM"
        else:
            color = ERROR_RED
            label = "LOW"

        data = [[f"Confidence Score: {percentage}% ({label})  "]]
        table = Table(data, colWidths=[170 * mm])
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 12),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("ROUNDED", (0, 0), (-1, -1), 4),
            ])
        )
        items.append(table)
        items.append(Spacer(1, 6 * mm))
        return items

    def _build_section(self, heading: str, content: str) -> list:
        items = []
        items.append(Paragraph(heading, self._styles["section_heading"]))
        items.append(Spacer(1, 2 * mm))
        items.append(Paragraph(content, self._styles["body_text"]))
        items.append(Spacer(1, 5 * mm))
        return items

    def _build_list_section(self, heading: str, items_list: list[str]) -> list:
        items = []
        items.append(Paragraph(heading, self._styles["section_heading"]))
        items.append(Spacer(1, 2 * mm))

        if not items_list:
            items.append(Paragraph("No items available.", self._styles["body_italic"]))
        else:
            list_items = [
                ListItem(Paragraph(item, self._styles["body_text"]), leftIndent=10)
                for item in items_list
            ]
            items.append(ListFlowable(list_items, bulletType="bullet", start="•"))

        items.append(Spacer(1, 5 * mm))
        return items

    # ── Page Decorations ──────────────────────────────────────────────────────

    def _add_header_footer(self, canvas, doc) -> None:  # noqa: ANN001
        canvas.saveState()
        page_width = A4[0]

        # Header bar
        canvas.setFillColor(DARK_BG)
        canvas.rect(0, A4[1] - 15 * mm, page_width, 15 * mm, fill=True, stroke=False)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(20 * mm, A4[1] - 10 * mm, "AI Error Diagnosis System")
        canvas.drawRightString(page_width - 20 * mm, A4[1] - 10 * mm, "Confidential — Internal Use Only")

        # Footer bar
        canvas.setFillColor(ACCENT_BLUE)
        canvas.rect(0, 0, page_width, 10 * mm, fill=True, stroke=False)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(20 * mm, 3 * mm, f"Page {doc.page}")
        canvas.drawRightString(
            page_width - 20 * mm, 3 * mm,
            f"Generated: {datetime.now().strftime('%Y-%m-%d')}"
        )

        canvas.restoreState()

    # ── Style Builder ─────────────────────────────────────────────────────────

    def _build_styles(self) -> dict[str, ParagraphStyle]:
        base = getSampleStyleSheet()
        styles: dict[str, ParagraphStyle] = {}

        styles["main_title"] = ParagraphStyle(
            "main_title",
            parent=base["Title"],
            fontSize=22,
            textColor=DARK_BG,
            spaceAfter=4,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )
        styles["sub_title"] = ParagraphStyle(
            "sub_title",
            parent=base["Heading2"],
            fontSize=14,
            textColor=HIGHLIGHT,
            spaceAfter=4,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )
        styles["meta_info"] = ParagraphStyle(
            "meta_info",
            parent=base["Normal"],
            fontSize=8,
            textColor=colors.grey,
            spaceAfter=6,
            alignment=TA_CENTER,
        )
        styles["section_heading"] = ParagraphStyle(
            "section_heading",
            parent=base["Heading3"],
            fontSize=12,
            textColor=ACCENT_BLUE,
            spaceBefore=6,
            spaceAfter=2,
            fontName="Helvetica-Bold",
        )
        styles["body_text"] = ParagraphStyle(
            "body_text",
            parent=base["Normal"],
            fontSize=9,
            textColor=TEXT_DARK,
            leading=14,
            spaceAfter=3,
        )
        styles["body_italic"] = ParagraphStyle(
            "body_italic",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.grey,
            leading=14,
            fontName="Helvetica-Oblique",
        )
        styles["footer_note"] = ParagraphStyle(
            "footer_note",
            parent=base["Normal"],
            fontSize=7,
            textColor=colors.grey,
            alignment=TA_CENTER,
        )
        return styles
