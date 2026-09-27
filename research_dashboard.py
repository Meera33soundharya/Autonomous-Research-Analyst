import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")

from app.graph.workflow import research_graph


st.set_page_config(
    page_title="Autonomous Multi-Agent Research Analyst",
    page_icon="??",
    layout="wide"
)

st.title("?? Autonomous Multi-Agent Research Analyst")
st.write("AI-powered research system using multiple autonomous agents.")

st.divider()

topic = st.text_area(
    "Enter your research topic",
    placeholder="Example: Electric Vehicles",
    height=100
)

if st.button("?? Start Autonomous Research", type="primary"):

    if not topic.strip():
        st.warning("Please enter a research topic.")
        st.stop()

    st.subheader("?? Research Pipeline")

    progress = st.progress(0)
    status = st.empty()

    try:

        status.info("?? Planner Agent — generating research questions...")
        progress.progress(10)

        result = research_graph.invoke(
            {"topic": topic.strip()}
        )

        progress.progress(100)

        status.success("? Research completed successfully.")

        st.divider()

        st.subheader("?? Research Questions")

        questions = result.get("research_questions", [])

        for i, question in enumerate(questions, 1):
            st.write(f"**{i}.** {question}")

        st.divider()

        st.subheader("?? Web Research")

        search_results = result.get("search_results", [])

        st.metric(
            "Web Sources Collected",
            len(search_results)
        )

        st.divider()

        st.subheader("?? Citation Verification")

        verified_evidence = result.get(
            "verified_evidence",
            []
        )

        supported = 0
        partial = 0
        unsupported = 0

        for group in verified_evidence:

            for finding in group.get("findings", []):

                finding_status = finding.get(
                    "status",
                    ""
                )

                if finding_status == "SUPPORTED":
                    supported += 1

                elif finding_status == "PARTIALLY_SUPPORTED":
                    partial += 1

                elif finding_status == "UNSUPPORTED":
                    unsupported += 1

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "? Supported",
                supported
            )

        with col2:
            st.metric(
                "?? Partially Supported",
                partial
            )

        with col3:
            st.metric(
                "? Unsupported",
                unsupported
            )

        st.divider()

        st.subheader("?? Final Research Report")

        report = result.get("report", "")

        if report:
            st.markdown(report)

        else:
            st.warning(
                "No report was generated."
            )

        st.divider()

        st.subheader("?? Download Reports")

        markdown_file = result.get(
            "markdown_file"
        )

        pdf_file = result.get(
            "pdf_file"
        )

        col1, col2 = st.columns(2)

        with col1:

            if markdown_file:

                markdown_path = Path(
                    markdown_file
                )

                if markdown_path.exists():

                    with open(
                        markdown_path,
                        "rb"
                    ) as file:

                        markdown_data = file.read()

                    st.download_button(
                        label="?? Download Markdown Report",
                        data=markdown_data,
                        file_name="research_report.md",
                        mime="text/markdown",
                        use_container_width=True
                    )

        with col2:

            if pdf_file:

                pdf_path = Path(
                    pdf_file
                )

                if pdf_path.exists():

                    with open(
                        pdf_path,
                        "rb"
                    ) as file:

                        pdf_data = file.read()

                    st.download_button(
                        label="?? Download PDF Report",
                        data=pdf_data,
                        file_name="research_report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

    except Exception as error:

        progress.empty()

        status.error(
            "? Research workflow failed."
        )

        st.exception(error)
