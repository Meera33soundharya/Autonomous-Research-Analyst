import streamlit as st

st.set_page_config(
    page_title="Autonomous Research Analyst",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 Autonomous Research Analyst")
st.write("Multi-Agent AI Research Dashboard")

st.divider()

topic = st.text_input(
    "Enter your research topic",
    placeholder="Example: Artificial Intelligence in Healthcare"
)

if st.button("🚀 Start Research"):
    if not topic.strip():
        st.warning("Please enter a research topic.")
    else:
        st.success(f"Research topic received: {topic}")

        st.subheader("Research Pipeline")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.info("🧠 Planner Agent")
            st.write("Generating research questions...")

        with col2:
            st.info("🔎 Searcher Agent")
            st.write("Collecting web sources...")

        with col3:
            st.info("📚 Researcher Agent")
            st.write("Analyzing evidence...")

        col4, col5, col6 = st.columns(3)

        with col4:
            st.info("🧹 Evidence Cleaner")
            st.write("Cleaning extracted evidence...")

        with col5:
            st.info("✅ Citation Checker")
            st.write("Checking source support...")

        with col6:
            st.info("✍️ Writer Agent")
            st.write("Preparing research report...")

        st.divider()

        st.subheader("📊 Research Status")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Research Questions", "5")

        with c2:
            st.metric("Web Sources", "15")

        with c3:
            st.metric("Pipeline", "Ready")

        st.divider()

        st.subheader("📄 Reports")

        st.write("After the research workflow completes:")

        st.code(
            "reports/research_report.md\n"
            "reports/research_report.pdf"
        )