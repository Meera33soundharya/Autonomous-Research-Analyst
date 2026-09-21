def generate_report(topic: str, verified_evidence: list[dict]) -> str:
    
    report = []

    report.append(f"# {topic}")
    report.append("")
    report.append("## 1. Executive Summary")
    report.append("")
    report.append(
        "This report summarizes the research evidence collected "
        "and verified by the autonomous research workflow."
    )
    report.append("")

    report.append("## 2. Introduction")
    report.append("")
    report.append(
        f"The research focuses on {topic}. "
        "The system collected sources, extracted claims, "
        "and checked whether the claims were supported by the available evidence."
    )
    report.append("")

    report.append("## 3. Key Findings")
    report.append("")

    for item in verified_evidence:

        report.append(
            f"### {item.get('question', '')}"
        )
        report.append("")

        for finding in item.get("findings", []):

            report.append(
                f"- **Claim:** {finding.get('claim', '')}"
            )

            report.append(
                f"- **Source:** {finding.get('source', '')}"
            )

            report.append(
                f"- **Status:** {finding.get('status', '')}"
            )

            report.append("")

    report.append("## 4. Evidence Analysis")
    report.append("")

    supported_count = 0
    unsupported_count = 0

    for item in verified_evidence:

        for finding in item.get("findings", []):

            if finding.get("status") == "SUPPORTED":
                supported_count += 1
            else:
                unsupported_count += 1

    report.append(
        f"Supported findings: {supported_count}"
    )

    report.append(
        f"Unsupported findings: {unsupported_count}"
    )

    report.append("")

    report.append("## 5. Challenges and Limitations")
    report.append("")
    report.append(
        "The report is limited to the sources collected by the research workflow. "
        "Claims without sufficient source information are not treated as verified."
    )
    report.append("")

    report.append("## 6. Future Opportunities")
    report.append("")
    report.append(
        "Future versions can improve source ranking, evidence extraction, "
        "citation verification, and report generation using stronger language models."
    )
    report.append("")

    report.append("## 7. Conclusion")
    report.append("")
    report.append(
        "The multi-agent workflow demonstrates how research questions, "
        "web sources, evidence extraction, citation verification, "
        "and report generation can be connected into an automated pipeline."
    )
    report.append("")

    report.append("## References")
    report.append("")

    for item in verified_evidence:

        for finding in item.get("findings", []):

            source = finding.get("source", "")
            url = finding.get("url", "")

            if source and url:
                report.append(
                    f"- {source}: {url}"
                )

    return "\n".join(report)