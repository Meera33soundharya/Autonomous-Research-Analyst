import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from app.agents.planner import create_research_plan
from app.agents.searcher import run_search
from app.agents.researcher import analyze_sources
from app.agents.citation_checker import check_citations
from app.agents.writer import generate_report
from app.services.report_service import save_markdown, save_pdf


st.set_page_config(
    page_title="Autonomous Research Analyst",
    page_icon="🔬",
    layout="wide"
)


st.title("🔬 Autonomous Research Analyst")

st.write(
    "Enter a research topic and let the AI agents "
    "plan, search, analyze, verify, and write the report."
)

st.divider()


topic = st.text_input(
    "Research Topic",
    placeholder="Example: Brain-Computer Interfaces"
)


if st.button("🚀 Start Research", type="primary"):

    if not topic.strip():
        st.warning("Please enter a research topic.")
        st.stop()

    topic = topic.strip()

    try:

        # --------------------------------------------------
        # 1. PLANNER
        # --------------------------------------------------

        planner_status = st.status(
            "🧠 Planner Agent running...",
            expanded=True
        )

        planner_status.write(
            "Generating research questions..."
        )

        research_questions = create_research_plan(topic)

        planner_status.write(
            f"Generated {len(research_questions)} research questions."
        )

        planner_status.update(
            label="🧠 Planner Agent completed",
            state="complete"
        )


        # --------------------------------------------------
        # 2. SEARCHER
        # --------------------------------------------------

        search_status = st.status(
            "🔍 Searcher Agent running...",
            expanded=True
        )

        search_status.write(
            "Searching current web sources..."
        )

        search_results = run_search(
            research_questions
        )

        search_status.write(
            f"Collected {len(search_results)} web sources."
        )

        search_status.update(
            label="🔍 Searcher Agent completed",
            state="complete"
        )


        # --------------------------------------------------
        # 3. RESEARCHER
        # --------------------------------------------------

        researcher_status = st.status(
            "🧠 Researcher Agent running...",
            expanded=True
        )

        evidence = []

        for index, question in enumerate(
            research_questions,
            start=1
        ):

            researcher_status.write(
                f"Analyzing question {index}/{len(research_questions)}..."
            )

            result = analyze_sources(
                question,
                search_results
            )

            evidence.append(result)

        researcher_status.write(
            f"Created {len(evidence)} evidence groups."
        )

        researcher_status.update(
            label="🧠 Researcher Agent completed",
            state="complete"
        )


        # --------------------------------------------------
        # 4. CITATION CHECKER
        # --------------------------------------------------

        citation_status = st.status(
            "🔎 Citation Checker running...",
            expanded=True
        )

        citation_status.write(
            "Verifying extracted evidence..."
        )

        verified_evidence = check_citations(
            evidence
        )

        total_findings = sum(
            len(item.get("findings", []))
            for item in verified_evidence
        )

        citation_status.write(
            f"Verified {total_findings} findings."
        )

        citation_status.update(
            label="🔎 Citation Checker completed",
            state="complete"
        )


        # --------------------------------------------------
        # 5. WRITER
        # --------------------------------------------------

        writer_status = st.status(
            "✍️ Writer Agent running...",
            expanded=True
        )

        writer_status.write(
            "Generating the final research report..."
        )

        report = generate_report(
            topic,
            verified_evidence
        )

        markdown_file = save_markdown(
            topic,
            report
        )

        pdf_file = save_pdf(
            topic,
            report
        )

        writer_status.write(
            "Markdown and PDF reports generated."
        )

        writer_status.update(
            label="✍️ Writer Agent completed",
            state="complete"
        )


        # --------------------------------------------------
        # SUCCESS
        # --------------------------------------------------

        st.success(
            "Research completed successfully! ✅"
        )

        st.divider()


        # --------------------------------------------------
        # TOPIC
        # --------------------------------------------------

        st.header("📌 Research Topic")

        st.write(topic)


        # --------------------------------------------------
        # QUESTIONS
        # --------------------------------------------------

        st.header("🧠 Research Questions")

        for question in research_questions:

            st.write(
                f"• {question}"
            )


        # --------------------------------------------------
        # VERIFIED EVIDENCE
        # --------------------------------------------------

        st.header("🔎 Verified Evidence")

        for item in verified_evidence:

            with st.expander(
                item["question"]
            ):

                findings = item.get(
                    "findings",
                    []
                )

                if not findings:

                    st.info(
                        "No evidence was extracted for this question."
                    )

                for finding in findings:

                    st.markdown("### Claim")

                    st.write(
                        finding.get(
                            "claim",
                            ""
                        )
                    )

                    st.markdown(
                        f"**Source:** "
                        f"{finding.get('source', '')}"
                    )

                    st.markdown(
                        f"**URL:** "
                        f"{finding.get('url', '')}"
                    )

                    status = finding.get(
                        "status",
                        "UNSUPPORTED"
                    )

                    score = finding.get(
                        "score",
                        0
                    )

                    reason = finding.get(
                        "reason",
                        ""
                    )

                    if status == "SUPPORTED":

                        st.success(
                            f"Status: {status} ✅ | "
                            f"Score: {score}"
                        )

                    elif status == "PARTIALLY_SUPPORTED":

                        st.warning(
                            f"Status: {status} ⚠️ | "
                            f"Score: {score}"
                        )

                    else:

                        st.error(
                            f"Status: {status} ❌ | "
                            f"Score: {score}"
                        )

                    if reason:

                        st.caption(
                            f"Reason: {reason}"
                        )

                    st.divider()


        # --------------------------------------------------
        # FINAL REPORT
        # --------------------------------------------------

        st.header("📄 Final Research Report")

        st.markdown(report)


        # --------------------------------------------------
        # DOWNLOAD
        # --------------------------------------------------

        st.download_button(
            label="⬇️ Download Markdown Report",
            data=report,
            file_name="research_report.md",
            mime="text/markdown"
        )


        st.success(
            f"PDF report saved to: {pdf_file}"
        )


    except Exception as e:

        st.error(
            "Research pipeline failed."
        )

        st.exception(e)