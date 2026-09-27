import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv


# ============================================================
# PROJECT / BACKEND SETUP
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

from app.graph.workflow import research_graph


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Research Intelligence Platform",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PROFESSIONAL CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ---------- GLOBAL ---------- */

    .stApp {
        background: #f6f8fc;
    }

    .main .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* ---------- HEADER ---------- */

    .hero {
        background: linear-gradient(
            135deg,
            #0f172a 0%,
            #1e3a8a 55%,
            #2563eb 100%
        );
        padding: 32px;
        border-radius: 18px;
        color: white;
        margin-bottom: 24px;
    }

    .hero-title {
        font-size: 34px;
        font-weight: 700;
        margin-bottom: 6px;
    }

    .hero-subtitle {
        font-size: 15px;
        color: #dbeafe;
        margin-bottom: 0;
    }

    /* ---------- SECTION TITLE ---------- */

    .section-title {
        font-size: 21px;
        font-weight: 700;
        color: #0f172a;
        margin-top: 10px;
        margin-bottom: 14px;
    }

    .section-subtitle {
        font-size: 13px;
        color: #64748b;
        margin-top: -8px;
        margin-bottom: 15px;
    }

    /* ---------- INPUT ---------- */

    .input-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 20px;
    }

    /* ---------- METRIC CARDS ---------- */

    .metric-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 20px;
        min-height: 120px;
    }

    .metric-label {
        color: #64748b;
        font-size: 13px;
        margin-bottom: 7px;
    }

    .metric-value {
        color: #0f172a;
        font-size: 29px;
        font-weight: 700;
    }

    /* ---------- PIPELINE ---------- */

    .pipeline-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px;
        min-height: 110px;
        text-align: center;
    }

    .pipeline-name {
        color: #0f172a;
        font-weight: 650;
        font-size: 14px;
        margin-top: 7px;
    }

    .pipeline-status {
        color: #16a34a;
        font-size: 12px;
        margin-top: 5px;
    }

    .pipeline-arrow {
        text-align: center;
        color: #94a3b8;
        font-size: 22px;
        padding-top: 35px;
    }

    /* ---------- QUESTION CARDS ---------- */

    .question-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 10px;
    }

    .question-number {
        color: #2563eb;
        font-weight: 700;
        font-size: 13px;
        margin-bottom: 5px;
    }

    .question-text {
        color: #0f172a;
        font-size: 14px;
        line-height: 1.55;
    }

    /* ---------- EVIDENCE ---------- */

    .evidence-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .evidence-label {
        color: #64748b;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }

    .evidence-claim {
        color: #0f172a;
        font-size: 14px;
        line-height: 1.6;
        margin-top: 5px;
    }

    .source-name {
        color: #475569;
        font-size: 13px;
        margin-top: 9px;
    }

    /* ---------- STATUS BADGES ---------- */

    .badge-supported {
        background: #dcfce7;
        color: #166534;
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 700;
        display: inline-block;
    }

    .badge-partial {
        background: #fef3c7;
        color: #92400e;
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 700;
        display: inline-block;
    }

    .badge-unsupported {
        background: #fee2e2;
        color: #991b1b;
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 700;
        display: inline-block;
    }

    /* ---------- SOURCE CARDS ---------- */

    .source-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 10px;
    }

    .source-title {
        color: #0f172a;
        font-size: 14px;
        font-weight: 650;
    }

    .source-url {
        color: #2563eb;
        font-size: 12px;
        word-break: break-all;
        margin-top: 6px;
    }

    /* ---------- SIDEBAR ---------- */

    section[data-testid="stSidebar"] {
        background: #0f172a;
    }

    section[data-testid="stSidebar"] * {
        color: #e2e8f0;
    }

    /* ---------- BUTTON ---------- */

    .stButton > button {
        border-radius: 10px;
        min-height: 44px;
        font-weight: 650;
    }

    /* ---------- REPORT ---------- */

    .report-shell {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 28px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="font-size:20px;font-weight:700;">
        Research Intelligence
        </div>
        <div style="font-size:12px;color:#94a3b8;margin-top:5px;">
        Autonomous multi-agent research platform
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### System")

    st.success("Backend Connected")

    st.markdown(
        """
        <div style="font-size:13px;line-height:1.9;">
        Planner Agent<br>
        Searcher Agent<br>
        Researcher Agent<br>
        Evidence Cleaner<br>
        Citation Checker<br>
        Writer Agent
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.caption("Powered by FastAPI, LangGraph, OpenRouter and Tavily")


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">
            Research Intelligence Platform
        </div>
        <div class="hero-subtitle">
            Autonomous multi-agent research, evidence verification,
            citation analysis and report generation.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TOPIC INPUT
# ============================================================

st.markdown(
    '<div class="section-title">Research Workspace</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-subtitle">'
    'Enter any topic and let the agent build the research workflow automatically.'
    '</div>',
    unsafe_allow_html=True,
)

topic = st.text_area(
    "Research Topic",
    placeholder="Example: Artificial Intelligence in Banking",
    height=90,
    label_visibility="collapsed",
)

start_research = st.button(
    "Start Autonomous Research",
    type="primary",
    use_container_width=True,
)


# ============================================================
# EXECUTE WORKFLOW
# ============================================================

if start_research:

    if not topic.strip():
        st.warning("Please enter a research topic.")
        st.stop()

    topic_clean = topic.strip()

    with st.spinner(
        "Running Planner -> Searcher -> Researcher -> "
        "Evidence Cleaner -> Citation Checker -> Writer..."
    ):

        try:

            result = research_graph.invoke(
                {"topic": topic_clean}
            )

            st.session_state["research_result"] = result

        except Exception as error:

            st.error("Research workflow failed.")
            st.exception(error)
            st.stop()


# ============================================================
# SHOW RESULT
# ============================================================

if "research_result" in st.session_state:

    result = st.session_state["research_result"]

    current_topic = result.get(
        "topic",
        topic if topic else "Research Topic"
    )

    questions = result.get(
        "research_questions",
        []
    )

    search_results = result.get(
        "search_results",
        []
    )

    verified_evidence = result.get(
        "verified_evidence",
        []
    )

    report = result.get(
        "report",
        ""
    )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    st.success(
        f"Research completed successfully for: {current_topic}"
    )

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    supported = 0
    partial = 0
    unsupported = 0
    total_findings = 0

    for group in verified_evidence:

        for finding in group.get("findings", []):

            total_findings += 1

            status = finding.get("status", "")

            if status == "SUPPORTED":
                supported += 1

            elif status == "PARTIALLY_SUPPORTED":
                partial += 1

            elif status == "UNSUPPORTED":
                unsupported += 1

    st.markdown(
        '<div class="section-title">Research Overview</div>',
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Research Questions</div>
                <div class="metric-value">{len(questions)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Web Sources</div>
                <div class="metric-value">{len(search_results)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Supported Findings</div>
                <div class="metric-value">{supported}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Total Findings</div>
                <div class="metric-value">{total_findings}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # --------------------------------------------------------
    # PIPELINE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Autonomous Research Pipeline</div>',
        unsafe_allow_html=True,
    )

    pipeline = [
        "Planner",
        "Searcher",
        "Researcher",
        "Evidence Cleaner",
        "Citation Checker",
        "Writer",
    ]

    cols = st.columns(len(pipeline))

    for index, name in enumerate(pipeline):

        with cols[index]:

            st.markdown(
                f"""
                <div class="pipeline-card">
                    <div style="font-size:22px;color:#2563eb;">
                        {index + 1}
                    </div>
                    <div class="pipeline-name">
                        {name}
                    </div>
                    <div class="pipeline-status">
                        Completed
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    # --------------------------------------------------------
    # TABS
    # --------------------------------------------------------

    tab_overview, tab_questions, tab_evidence, tab_report, tab_sources = st.tabs(
        [
            "Overview",
            "Research Questions",
            "Verified Evidence",
            "Final Report",
            "Sources",
        ]
    )

    # ========================================================
    # OVERVIEW
    # ========================================================

    with tab_overview:

        st.markdown(
            '<div class="section-title">Research Status</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Supported", supported)

        with c2:
            st.metric("Partially Supported", partial)

        with c3:
            st.metric("Unsupported", unsupported)

        st.divider()

        st.markdown(
            f"""
            <div class="report-shell">
                <h3 style="margin-top:0;color:#0f172a;">
                    Research Topic
                </h3>
                <p style="color:#475569;font-size:15px;">
                    {current_topic}
                </p>
                <p style="color:#64748b;font-size:13px;">
                    The system dynamically planned research questions,
                    collected web sources, extracted evidence, verified
                    citations and generated the final report.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ========================================================
    # QUESTIONS
    # ========================================================

    with tab_questions:

        st.markdown(
            '<div class="section-title">Generated Research Questions</div>',
            unsafe_allow_html=True,
        )

        for index, question in enumerate(
            questions,
            1
        ):

            st.markdown(
                f"""
                <div class="question-card">
                    <div class="question-number">
                        QUESTION {index}
                    </div>
                    <div class="question-text">
                        {question}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ========================================================
    # EVIDENCE
    # ========================================================

    with tab_evidence:

        st.markdown(
            '<div class="section-title">Evidence Verification</div>',
            unsafe_allow_html=True,
        )

        for group in verified_evidence:

            group_question = group.get(
                "question",
                "Research Question"
            )

            st.markdown(
                f"""
                <div style="
                    font-size:16px;
                    font-weight:700;
                    color:#0f172a;
                    margin-top:10px;
                    margin-bottom:12px;
                ">
                    {group_question}
                </div>
                """,
                unsafe_allow_html=True,
            )

            for finding in group.get(
                "findings",
                []
            ):

                claim = finding.get(
                    "claim",
                    "No claim available."
                )

                source = finding.get(
                    "source",
                    finding.get(
                        "source_title",
                        "Unknown Source"
                    )
                )

                status = finding.get(
                    "status",
                    "UNSUPPORTED"
                )

                if status == "SUPPORTED":

                    badge = (
                        '<span class="badge-supported">'
                        'SUPPORTED'
                        '</span>'
                    )

                elif status == "PARTIALLY_SUPPORTED":

                    badge = (
                        '<span class="badge-partial">'
                        'PARTIALLY SUPPORTED'
                        '</span>'
                    )

                else:

                    badge = (
                        '<span class="badge-unsupported">'
                        'UNSUPPORTED'
                        '</span>'
                    )

                st.markdown(
                    f"""
                    <div class="evidence-card">

                        <div class="evidence-label">
                            Claim
                        </div>

                        <div class="evidence-claim">
                            {claim}
                        </div>

                        <div class="source-name">
                            Source: {source}
                        </div>

                        <div style="margin-top:10px;">
                            {badge}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    with tab_report:

        st.markdown(
            '<div class="section-title">Final Research Report</div>',
            unsafe_allow_html=True,
        )

        if report:

            st.markdown(
                '<div class="report-shell">',
                unsafe_allow_html=True,
            )

            st.markdown(report)

            st.markdown(
                '</div>',
                unsafe_allow_html=True,
            )

        else:

            st.warning(
                "No report was generated."
            )

    # ========================================================
    # SOURCES
    # ========================================================

    with tab_sources:

        st.markdown(
            '<div class="section-title">Web Research Sources</div>',
            unsafe_allow_html=True,
        )

        seen_urls = set()

        for index, source in enumerate(
            search_results,
            1
        ):

            title = source.get(
                "title",
                "Untitled Source"
            )

            url = source.get(
                "url",
                ""
            )

            question = source.get(
                "question",
                ""
            )

            if url in seen_urls:
                continue

            seen_urls.add(url)

            st.markdown(
                f"""
                <div class="source-card">

                    <div class="source-title">
                        {index}. {title}
                    </div>

                    <div class="source-url">
                        {url}
                    </div>

                    <div style="
                        color:#64748b;
                        font-size:12px;
                        margin-top:8px;
                    ">
                        Research Question: {question}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    # ========================================================
    # DOWNLOADS
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">Download Reports</div>',
        unsafe_allow_html=True,
    )

    markdown_file = result.get(
        "markdown_file"
    )

    pdf_file = result.get(
        "pdf_file"
    )

    d1, d2 = st.columns(2)

    with d1:

        if markdown_file:

            markdown_path = Path(
                markdown_file
            )

            if markdown_path.exists():

                with open(
                    markdown_path,
                    "rb"
                ) as file:

                    st.download_button(
                        "Download Markdown Report",
                        file.read(),
                        file_name="research_report.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )

    with d2:

        if pdf_file:

            pdf_path = Path(
                pdf_file
            )

            if pdf_path.exists():

                with open(
                    pdf_path,
                    "rb"
                ) as file:

                    st.download_button(
                        "Download PDF Report",
                        file.read(),
                        file_name="research_report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )