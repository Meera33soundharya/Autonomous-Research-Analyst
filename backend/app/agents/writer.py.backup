import re


def clean_report_text(text: str) -> str:
    """Clean spacing and webpage extraction artifacts."""

    if not text:
        return ""

    replacements = {
        "invarious": "in various",
        "andpotential": "and potential",
        "careapproaches": "care approaches",
        "theevidence": "the evidence",
        "sourcecontent": "source content",
        "AReview": "A Review",
        "healthcarebalance": "healthcare balance",
        "healthcareAI": "healthcare AI",
        "patientmonitoring": "patient monitoring",
        "patientcare": "patient care",
        "patientrecords": "patient records",
        "clinicaldecision": "clinical decision",
        "medicalimaging": "medical imaging",
        "drugdiscovery": "drug discovery",
        "clinicalsettings": "clinical settings",
        "safetyrisks": "safety risks",
        "accountability.Inaccuracies": "accountability. Inaccuracies",
        "biasagainst": "bias against",
        "downstreamuse": "downstream use",
        "underrepresented": "underrepresented",
        "workforce-related": "workforce-related",
        "technical, financial": "technical, financial",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(
        r'\s+',
        ' ',
        text
    )

    text = re.sub(
        r'\s+([,.!?;:])',
        r'\1',
        text
    )

    text = re.sub(
        r'([,.!?;:])([A-Za-z])',
        r'\1 \2',
        text
    )

    return text.strip()


def generate_report(
    topic: str,
    verified_evidence: list[dict]
) -> str:
    """Generate the final research report."""

    report = []

    report.append(
        f"# {topic}"
    )

    report.append("")

    report.append(
        "## 1. Executive Summary"
    )

    report.append("")

    supported_count = 0
    partial_count = 0
    unsupported_count = 0

    for item in verified_evidence:

        for finding in item.get(
            "findings",
            []
        ):

            status = finding.get(
                "status",
                ""
            ).upper()

            if status == "SUPPORTED":
                supported_count += 1

            elif status == "PARTIALLY_SUPPORTED":
                partial_count += 1

            elif status == "UNSUPPORTED":
                unsupported_count += 1

    total_verified = (
        supported_count
        + partial_count
    )

    report.append(
        f"This report presents research findings about "
        f"{topic}. The autonomous research workflow "
        f"collected web sources, extracted evidence, "
        f"and checked the evidence against its source "
        f"content."
    )

    report.append("")

    report.append(
        f"The workflow identified {total_verified} "
        f"findings with supporting or partial source "
        f"evidence. {supported_count} findings were "
        f"classified as supported and {partial_count} "
        f"findings were classified as partially supported."
    )

    report.append("")

    report.append(
        "## 2. Introduction"
    )

    report.append("")

    report.append(
        f"The research focuses on {topic}. The system "
        f"generated research questions, collected web "
        f"sources, extracted relevant evidence, and "
        f"evaluated the relationship between each claim "
        f"and its source content."
    )

    report.append("")

    report.append(
        "## 3. Key Findings"
    )

    report.append("")

    references = []
    seen_references = set()

    for item in verified_evidence:

        question = clean_report_text(
            item.get(
                "question",
                ""
            ).strip()
        )

        valid_findings = []

        for finding in item.get(
            "findings",
            []
        ):

            status = finding.get(
                "status",
                ""
            ).upper()

            if status not in [
                "SUPPORTED",
                "PARTIALLY_SUPPORTED"
            ]:
                continue

            claim = clean_report_text(
                finding.get(
                    "claim",
                    ""
                ).strip()
            )

            source = clean_report_text(
                finding.get(
                    "source",
                    ""
                ).strip()
            )

            url = finding.get(
                "url",
                ""
            ).strip()

            if not claim:
                continue

            valid_findings.append({
                "claim": claim,
                "source": source,
                "url": url,
                "status": status
            })

            reference_key = (
                source,
                url
            )

            if (
                source
                and url
                and reference_key
                not in seen_references
            ):

                seen_references.add(
                    reference_key
                )

                references.append({
                    "source": source,
                    "url": url
                })

        if not valid_findings:
            continue

        report.append(
            f"### {question}"
        )

        report.append("")

        for finding in valid_findings:

            report.append(
                f"- **Claim:** {finding['claim']}"
            )

            report.append(
                f"- **Source:** {finding['source']}"
            )

            report.append(
                f"- **Status:** {finding['status']}"
            )

            report.append("")

    report.append(
        "## 4. Evidence Analysis"
    )

    report.append("")

    report.append(
        f"Supported findings: {supported_count}"
    )

    report.append(
        f"Partially supported findings: {partial_count}"
    )

    report.append(
        f"Unsupported findings excluded from report: "
        f"{unsupported_count}"
    )

    report.append("")

    report.append(
        "Only supported and partially supported findings "
        "are included in the main research report. "
        "Unsupported findings are excluded from the "
        "report content."
    )

    report.append("")

    report.append(
        "## 5. Challenges and Limitations"
    )

    report.append("")

    report.append(
        "The report is limited to the sources collected "
        "by the research workflow. The citation checker "
        "evaluates whether the extracted claim has "
        "textual support in the collected source content. "
        "A partially supported finding should therefore "
        "not be interpreted as complete verification."
    )

    report.append("")

    if unsupported_count > 0:

        report.append(
            f"The workflow identified "
            f"{unsupported_count} unsupported findings. "
            f"These findings were excluded from the main "
            f"research report."
        )

        report.append("")

    report.append(
        "## 6. Future Opportunities"
    )

    report.append("")

    report.append(
        "Future versions can improve source ranking, "
        "evidence extraction, semantic citation "
        "verification, duplicate detection, source "
        "credibility assessment, and report generation."
    )

    report.append("")

    report.append(
        "## 7. Conclusion"
    )

    report.append("")

    report.append(
        f"The autonomous research workflow demonstrates "
        f"how research questions, web search, evidence "
        f"extraction, citation checking, and report "
        f"generation can be connected into an automated "
        f"research pipeline for the topic of {topic}."
    )

    report.append("")

    report.append(
        f"The final report contains {total_verified} "
        f"findings that passed the minimum "
        f"evidence-support criteria."
    )

    report.append("")

    report.append(
        "## References"
    )

    report.append("")

    if references:

        for reference in references:

            report.append(
                f"- {reference['source']}: "
                f"{reference['url']}"
            )

    else:

        report.append(
            "No verified source references were available."
        )

    report.append("")

    return "\n".join(report)