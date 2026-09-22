from pathlib import Path
from html import escape

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]

REPORTS_DIR = PROJECT_ROOT / "reports"

REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def save_markdown(topic: str, report: str) -> str:

    filepath = REPORTS_DIR / "research_report.md"

    filepath.write_text(
        report,
        encoding="utf-8"
    )

    return str(filepath)


def save_pdf(topic: str, report: str) -> str:

    filepath = REPORTS_DIR / "research_report.pdf"

    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    story = []

    for line in report.splitlines():

        line = line.strip()

        if not line:
            story.append(
                Spacer(1, 8)
            )
            continue

        # Main title
        if line.startswith("# "):

            text = escape(line[2:].strip())

            story.append(
                Paragraph(
                    text,
                    styles["Title"]
                )
            )

        # Section heading
        elif line.startswith("## "):

            text = escape(line[3:].strip())

            story.append(
                Paragraph(
                    text,
                    styles["Heading2"]
                )
            )

        # Sub-heading
        elif line.startswith("### "):

            text = escape(line[4:].strip())

            story.append(
                Paragraph(
                    text,
                    styles["Heading3"]
                )
            )

        # Bullet
        elif line.startswith("- "):

            text = escape(line[2:].strip())

            story.append(
                Paragraph(
                    "• " + text,
                    styles["BodyText"]
                )
            )

        else:

            text = escape(line)

            story.append(
                Paragraph(
                    text,
                    styles["BodyText"]
                )
            )

        story.append(
            Spacer(1, 5)
        )

    doc.build(story)

    return str(filepath)