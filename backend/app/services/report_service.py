from pathlib import Path

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"

REPORTS_DIR.mkdir(exist_ok=True)


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
        pagesize=A4
    )

    styles = getSampleStyleSheet()

    story = []

    for line in report.splitlines():

        line = line.strip()

        if not line:
            story.append(Spacer(1, 8))
            continue

        if line.startswith("# "):

            story.append(
                Paragraph(
                    line[2:],
                    styles["Title"]
                )
            )

        elif line.startswith("## "):

            story.append(
                Paragraph(
                    line[3:],
                    styles["Heading2"]
                )
            )

        else:

            story.append(
                Paragraph(
                    line,
                    styles["BodyText"]
                )
            )

        story.append(
            Spacer(1, 5)
        )

    doc.build(story)

    return str(filepath)