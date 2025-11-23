"""PDF export functionality."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from nyx.core.logger import get_logger

logger = get_logger(__name__)


class PDFExporter:
    """Export OSINT data to PDF format."""

    def __init__(self, page_size: str = "letter") -> None:
        """Initialize PDF exporter.

        Args:
            page_size: Page size ('letter' or 'a4')
        """
        self.page_size = letter if page_size == "letter" else A4
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self) -> None:
        """Setup custom styles."""
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#1a1a1a"),
                spaceAfter=30,
                alignment=TA_CENTER,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="CustomHeading",
                parent=self.styles["Heading2"],
                fontSize=16,
                textColor=colors.HexColor("#333333"),
                spaceAfter=12,
                spaceBefore=12,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="Metadata",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#666666"),
                spaceAfter=6,
            )
        )

    def export(
        self,
        data: Dict[str, Any],
        output_path: str,
        title: str = "OSINT Investigation Report",
        description: str = "",
        redact_fields: Optional[List[str]] = None,
    ) -> None:
        """Export data to PDF.

        Args:
            data: Data to export
            output_path: Output file path
            title: Report title
            description: Report description
            redact_fields: Fields to redact
        """
        try:
            if redact_fields:
                data = self._redact_fields(data, redact_fields)

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            doc = SimpleDocTemplate(
                output_path,
                pagesize=self.page_size,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            story = []

            story.append(Paragraph(title, self.styles["CustomTitle"]))
            story.append(Spacer(1, 0.2 * inch))

            metadata_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            story.append(Paragraph(metadata_text, self.styles["Metadata"]))

            if description:
                story.append(Paragraph(description, self.styles["Metadata"]))

            story.append(Spacer(1, 0.3 * inch))

            if data.get("profiles"):
                story.append(Paragraph("Profiles", self.styles["CustomHeading"]))
                story.append(Spacer(1, 0.1 * inch))

                for profile in data["profiles"]:
                    profile_data = []
                    for key, value in profile.items():
                        if value:
                            profile_data.append([key.title(), str(value)])

                    if profile_data:
                        table = Table(profile_data, colWidths=[2 * inch, 4 * inch])
                        table.setStyle(
                            TableStyle(
                                [
                                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                ]
                            )
                        )
                        story.append(table)
                        story.append(Spacer(1, 0.2 * inch))

            if data.get("data"):
                story.append(Paragraph("Additional Data", self.styles["CustomHeading"]))
                story.append(Spacer(1, 0.1 * inch))

                if data["data"]:
                    headers = list(data["data"][0].keys())
                    table_data = [headers]

                    for item in data["data"]:
                        row = [str(item.get(h, "")) for h in headers]
                        table_data.append(row)

                    table = Table(table_data)
                    table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#007bff")),
                                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                ("FONTSIZE", (0, 0), (-1, -1), 9),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                                ("TOPPADDING", (0, 0), (-1, -1), 6),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                            ]
                        )
                    )
                    story.append(table)

            story.append(PageBreak())

            footer_text = f"Generated by Nyx OSINT Platform v0.1.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            story.append(Paragraph(footer_text, self.styles["Metadata"]))

            doc.build(story)

            logger.info(f"Exported PDF report to {output_path}")

        except Exception as e:
            logger.error(f"Failed to export PDF: {e}")
            raise

    def _redact_fields(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Redact specified fields.

        Args:
            data: Data to redact
            fields: Fields to redact

        Returns:
            Redacted data
        """
        import copy

        redacted = copy.deepcopy(data)

        def redact_recursive(obj: Any) -> Any:
            if isinstance(obj, dict):
                for key in list(obj.keys()):
                    if key in fields:
                        obj[key] = "[REDACTED]"
                    else:
                        obj[key] = redact_recursive(obj[key])
            elif isinstance(obj, list):
                return [redact_recursive(item) for item in obj]
            return obj

        return redact_recursive(redacted)
