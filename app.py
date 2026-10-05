import sys
import time
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

import dashboard
import store


ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")

st.set_page_config(
    page_title="Research Intelligence Platform",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGE_OPTIONS = ("Dashboard", "New research", "Research history", "Reports")
PAGE_CSS = """
<style>
:root{color-scheme:dark}
.stApp{background:#0b1020;color:#e8eefc}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{background:#0d1427;border-right:1px solid #242f4d}
[data-testid="stSidebar"] *{color:#e8eefc}
.block-container{max-width:1440px;padding-top:2rem;padding-bottom:3rem}
h1,h2,h3,p,label{color:#e8eefc}
[data-testid="stCaptionContainer"],.stCaption{color:#a8b4cf}
input,textarea,[data-baseweb="select"]>div{background:#131b30!important;border-color:#34405d!important;color:#e8eefc!important}
button:focus-visible,input:focus-visible,textarea:focus-visible,[role="radio"]:focus-visible{outline:3px solid #9db2ff!important;outline-offset:3px!important}
button[kind="primary"]{background:#6b8cff;border:1px solid #6b8cff;color:#0b1020}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid #242f4d;border-radius:12px;overflow:hidden}
@media(max-width:900px){.block-container{padding-left:1rem;padding-right:1rem}}
</style>
"""

research_graph = None
BACKEND_ERROR = ""
LANGGRAPH_AVAILABLE = False
try:
    import langgraph.graph  # noqa: F401

    LANGGRAPH_AVAILABLE = True
except Exception as error:
    BACKEND_ERROR = f"{type(error).__name__}: {error}"

try:
    from app.graph.workflow import research_graph
except Exception as error:
    BACKEND_ERROR = f"{type(error).__name__}: {error}"


def flatten_html(markup: str) -> str:
    return "".join(line.strip() for line in markup.splitlines())


st.markdown(flatten_html(PAGE_CSS), unsafe_allow_html=True)


def _system_status() -> list[tuple[str, str]]:
    backend = "Ready" if research_graph is not None else "Unavailable"
    openrouter = "Ready" if os.getenv("OPENROUTER_API_KEY") else "No key"
    tavily = "Ready" if os.getenv("TAVILY_API_KEY") else "No key"
    langgraph = "Ready" if LANGGRAPH_AVAILABLE else "Unavailable"
    return [
        ("Backend", backend),
        ("OpenRouter", openrouter),
        ("Tavily", tavily),
        ("LangGraph", langgraph),
    ]


def _render_iframe(markup: str, fallback_height: int = 500) -> None:
    if callable(getattr(st, "iframe", None)):
        st.iframe(markup, height="content")
        return
    import streamlit.components.v1 as components

    components.html(markup, height=fallback_height, scrolling=False)


def _error(message: str, title: str = "Something went wrong") -> None:
    _render_iframe(dashboard.error_card_html(message, title), fallback_height=110)


def _read_runs() -> list[dict[str, Any]]:
    try:
        runs = store.load_runs()
    except RuntimeError as error:
        _error(str(error), "Saved research data unavailable")
        return []
    return runs


def _sidebar() -> str:
    with st.sidebar:
        st.markdown(
            flatten_html(
                '<div style="padding:8px 2px 20px;border-bottom:1px solid #242f4d;margin-bottom:18px">'
                '<div style="font-size:19px;font-weight:750;letter-spacing:-.02em">✦ Research Intelligence</div>'
                '<div style="font-size:12px;color:#a8b4cf;margin-top:4px">Autonomous research workspace</div></div>'
                '<div style="font-size:10px;color:#a8b4cf;font-weight:700;letter-spacing:.12em;margin:0 0 8px">WORKSPACE</div>'
            ),
            unsafe_allow_html=True,
        )
        page = st.radio(
            "Workspace",
            PAGE_OPTIONS,
            key="navigation_page",
            label_visibility="collapsed",
        )
        st.markdown(
            flatten_html(
                '<div style="font-size:10px;color:#a8b4cf;font-weight:700;letter-spacing:.12em;'
                'margin:24px 0 10px">SYSTEM</div>'
            ),
            unsafe_allow_html=True,
        )
        for name, status in _system_status():
            color = "#3ddc97" if status == "Ready" else "#ff6b85"
            st.markdown(
                flatten_html(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;'
                    f'font-size:12px;padding:6px 1px"><span>{name}</span>'
                    f'<span style="color:{color};font-weight:650">{status}</span></div>'
                ),
                unsafe_allow_html=True,
            )
    return page


def _summary(topic: str, state: dict[str, Any], statuses: dict[str, str], elapsed: float, status: str, error: str = "") -> dict[str, Any]:
    claims = dashboard.get_claims(state)
    sources = dashboard.get_sources(state)
    supported, partial, unsupported = dashboard.count_verdicts(claims)
    judged = supported + partial + unsupported
    created = datetime.now().astimezone().isoformat()
    return {
        "id": str(uuid.uuid4()),
        "topic": topic,
        "date": created,
        "created": created,
        "status": status,
        "seconds": round(elapsed, 2),
        "n_sources": len(sources),
        "n_claims": len(claims),
        "supported": supported,
        "partial": partial,
        "unsupported": unsupported,
        "accuracy": round(100 * supported / judged) if judged else None,
        "claims": claims,
        "sources": sources,
        "questions": dashboard.get_questions(state),
        "report": str(state.get("report") or ""),
        "agents": dict(statuses),
        "error": error,
        "result": state,
    }


def _render_live_outputs(
    state: dict[str, Any],
    status: dict[str, str],
    topic: str,
    active_agent: str,
    elapsed: float,
    panel: Any,
    questions_slot: Any,
    claims_slot: Any,
    report_slot: Any,
) -> None:
    panel.iframe(dashboard.agent_panel_html(status, "Active pipeline", "Updating after every agent"), height="content")
    questions = dashboard.get_questions(state)
    if questions:
        questions_slot.table({"Research questions": questions})
    else:
        questions_slot.info("Research questions will appear after the Planner finishes.")
    claims = dashboard.claims_table_rows(dashboard.get_claims(state))
    if claims:
        claims_slot.dataframe(claims, use_container_width=True, hide_index=True)
    else:
        claims_slot.info("Verified claims will appear after the Citation Checker finishes.")
    report = state.get("report")
    if report:
        report_slot.markdown(report)
    elif active_agent == "writer":
        report_slot.info("The Writer is preparing the final report.")
    st.session_state["active_pipeline"] = {
        "topic": topic,
        "status": dict(status),
        "elapsed": elapsed,
    }


def _execute_research(topic: str) -> dict[str, Any]:
    statuses = {key: "Waiting" for key in dashboard.AGENT_KEYS}
    live_state: dict[str, Any] = {"topic": topic}
    started = time.monotonic()
    active_agent = dashboard.AGENT_KEYS[0]
    statuses[active_agent] = "Running"
    active_panel = st.empty()
    live_header = st.empty()
    with st.container():
        st.markdown("#### Research questions")
        questions_slot = st.empty()
        st.markdown("#### Verified claims")
        claims_slot = st.empty()
        st.markdown("#### Final report")
        report_slot = st.empty()

    if research_graph is None:
        error = BACKEND_ERROR or "The research workflow could not be loaded."
        statuses[active_agent] = "Failed"
        st.session_state["active_pipeline"] = {
            "topic": topic,
            "status": dict(statuses),
            "elapsed": time.monotonic() - started,
        }
        run = _summary(topic, live_state, statuses, time.monotonic() - started, "Failed", error)
        try:
            store.save_run(run)
        except RuntimeError as save_error:
            _error(f"{error}\n\nCould not save the failed run: {save_error}")
            return run
        _error(error)
        return run

    _render_live_outputs(
        live_state, statuses, topic, active_agent, 0, active_panel, questions_slot, claims_slot, report_slot
    )
    try:
        for update in research_graph.stream({"topic": topic}, stream_mode="updates"):
            for node_name, node_state in update.items():
                if node_name in statuses:
                    statuses[node_name] = "Completed"
                if isinstance(node_state, dict):
                    live_state.update(node_state)
                try:
                    completed_index = dashboard.AGENT_KEYS.index(node_name)
                    next_agent = dashboard.AGENT_KEYS[completed_index + 1]
                except (ValueError, IndexError):
                    next_agent = ""
                if next_agent and statuses[next_agent] == "Waiting":
                    statuses[next_agent] = "Running"
                    active_agent = next_agent
            elapsed = time.monotonic() - started
            live_header.iframe(
                dashboard.live_header_html(topic, active_agent.replace("_", " ").title(), elapsed),
                height="content",
            )
            _render_live_outputs(
                live_state,
                statuses,
                topic,
                active_agent,
                elapsed,
                active_panel,
                questions_slot,
                claims_slot,
                report_slot,
            )

        elapsed = time.monotonic() - started
        run = _summary(topic, live_state, statuses, elapsed, "Completed")
        store.save_run(run)
        st.session_state["latest_run_id"] = run["id"]
        st.success(f"Research completed in {elapsed:.1f} seconds.")
        return run
    except Exception as error:
        elapsed = time.monotonic() - started
        if active_agent in statuses and statuses[active_agent] == "Running":
            statuses[active_agent] = "Failed"
        message = f"{type(error).__name__}: {error}"
        st.session_state["active_pipeline"] = {
            "topic": topic,
            "status": dict(statuses),
            "elapsed": elapsed,
        }
        active_panel.iframe(
            dashboard.agent_panel_html(statuses, "Active pipeline", "Run stopped with an agent error"),
            height="content",
        )
        run = _summary(topic, live_state, statuses, elapsed, "Failed", message)
        try:
            store.save_run(run)
            st.session_state["latest_run_id"] = run["id"]
        except RuntimeError as save_error:
            message = f"{message}\n\nCould not save the failed run: {save_error}"
        _error(message)
        return run


def _dataframe(rows: list[dict[str, Any]], empty_message: str) -> None:
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info(empty_message)


def _render_run_details(run: dict[str, Any], include_error: bool = True) -> None:
    if include_error and run.get("error"):
        _error(str(run["error"]))
    state = run.get("result") if isinstance(run.get("result"), dict) else {}
    questions = run.get("questions") or dashboard.get_questions(state)
    claims = run.get("claims") or dashboard.get_claims(state)
    sources = run.get("sources") or dashboard.get_sources(state)
    report = run.get("report") or state.get("report") or ""

    st.markdown(f"**Topic:** {run.get('topic', 'Research')}")
    st.caption(
        f"{run.get('status', 'Unknown')} · {run.get('seconds', 0)}s · "
        f"{run.get('date') or run.get('created') or 'Date unavailable'}"
    )
    question_tab, claim_tab, source_tab = st.tabs(("Questions", "Claims", "Sources"))
    with question_tab:
        _dataframe(
            [{"Research question": question} for question in questions],
            "No research questions are available for this run.",
        )
    with claim_tab:
        _dataframe(
            dashboard.claims_table_rows(claims),
            "No verified claims are available for this run.",
        )
    with source_tab:
        _dataframe(
            dashboard.sources_table_rows(sources),
            "No sources are available for this run.",
        )
    st.markdown("#### Final report")
    if report:
        st.markdown(str(report))
    else:
        st.info("No final report is available for this run.")


def _open_new_research() -> None:
    topic = str(st.session_state.get("dashboard_topic", "")).strip()
    if topic:
        st.session_state["research_topic"] = topic
        st.session_state["navigation_page"] = "New research"


def dashboard_page(runs: list[dict[str, Any]]) -> None:
    st.title("Research Intelligence")
    st.caption("Track autonomous research, source coverage, and evidence quality.")
    with st.form("dashboard_new_research", clear_on_submit=False):
        topic = st.text_input(
            "Research topic",
            placeholder="e.g. Evidence-based evaluation of retrieval-augmented generation",
            key="dashboard_topic",
        )
        submitted = st.form_submit_button(
            "New research",
            type="primary",
            on_click=_open_new_research,
        )
    if submitted:
        if not topic.strip():
            st.warning("Enter a topic to start a research run.")
    if runs and runs[0].get("status") == "Failed" and runs[0].get("error"):
        _error(str(runs[0]["error"]), "Latest research run failed")
    active = st.session_state.get("active_pipeline") or {}
    statuses = active.get("status") if active else None
    _render_iframe(dashboard.dashboard_html(runs, statuses))


def new_research_page(runs: list[dict[str, Any]]) -> None:
    st.title("New research")
    st.caption("Follow each agent as it builds and verifies your report.")
    default_topic = st.session_state.get("research_topic", "")
    with st.form("new_research_form"):
        topic = st.text_area(
            "Research topic",
            value=default_topic,
            height=90,
            placeholder="Describe the topic you want the agents to investigate.",
        )
        submitted = st.form_submit_button("Start research", type="primary")
    if submitted:
        if not topic.strip():
            st.warning("Enter a topic before starting the research pipeline.")
        else:
            st.session_state["research_topic"] = topic.strip()
            _execute_research(topic.strip())
    latest = runs[0] if runs else None
    if latest:
        st.markdown("### Latest run")
        _render_run_details(latest)
    else:
        _render_iframe(
            dashboard.empty_state_html(
                "No research runs yet",
                "Enter a topic above to run the six-agent research pipeline.",
            ),
            fallback_height=100,
        )
    if research_graph is None:
        _error(BACKEND_ERROR or "The research workflow is unavailable.", "Backend unavailable")


def history_page(runs: list[dict[str, Any]]) -> None:
    st.title("Research history")
    st.caption("Review, inspect, and remove saved research runs.")
    if not runs:
        _render_iframe(
            dashboard.empty_state_html(
                "Your history is empty",
                "Completed and failed research runs will be saved here.",
            ),
            fallback_height=100,
        )
        return

    summary_rows = [
        {
            "Topic": str(run.get("topic") or "Research"),
            "Status": str(run.get("status") or "Unknown"),
            "Sources": int(run.get("n_sources", 0) or 0),
            "Claims": int(run.get("n_claims", 0) or 0),
            "Accuracy": f"{run['accuracy']}%" if run.get("accuracy") is not None else "—",
            "Duration": f"{float(run.get('seconds', 0) or 0):.1f}s",
            "Date": str(run.get("date") or run.get("created") or "Unknown"),
        }
        for run in runs
    ]
    st.dataframe(summary_rows, use_container_width=True, hide_index=True)
    run_ids = [str(run.get("id")) for run in runs]
    if st.session_state.get("history_run_id") not in run_ids:
        st.session_state["history_run_id"] = run_ids[0]
    selected_id = st.selectbox(
        "Inspect a run",
        run_ids,
        key="history_run_id",
        format_func=lambda run_id: next(
            (
                f"{run.get('topic', 'Research')} · {run.get('status', 'Unknown')}"
                for run in runs
                if str(run.get("id")) == run_id
            ),
            "Research run",
        ),
    )
    selected = next(run for run in runs if str(run.get("id")) == selected_id)
    if st.button("Delete selected run"):
        try:
            store.delete_run(selected_id)
        except RuntimeError as error:
            _error(str(error), "Could not delete research run")
        else:
            st.session_state.pop("history_run_id", None)
            st.rerun()
    _render_run_details(selected)


def reports_page(runs: list[dict[str, Any]]) -> None:
    st.title("Reports")
    st.caption("Read and download Markdown reports generated by the research agents.")
    reports = [run for run in runs if run.get("report")]
    if not reports:
        latest_failed = next(
            (run for run in runs if run.get("status") == "Failed" and run.get("error")),
            None,
        )
        if latest_failed:
            _error(str(latest_failed["error"]), "Latest research run failed")
        _render_iframe(
            dashboard.empty_state_html(
                "No reports available",
                "A report appears here after a research run completes successfully.",
            ),
            fallback_height=100,
        )
        return
    report_ids = [str(run.get("id")) for run in reports]
    selected_id = st.selectbox(
        "Select a saved report",
        report_ids,
        format_func=lambda run_id: next(
            (str(run.get("topic", "Research")) for run in reports if str(run.get("id")) == run_id),
            "Research report",
        ),
        key="selected_report_id",
    )
    selected = next(run for run in reports if str(run.get("id")) == selected_id)
    report = str(selected.get("report") or "")
    st.markdown(f"### {selected.get('topic', 'Research report')}")
    if report:
        st.markdown(report)
    else:
        st.info("The selected run does not contain report text.")
    st.download_button(
        "Download Markdown",
        data=report,
        file_name=f"{selected.get('topic', 'research-report')}.md",
        mime="text/markdown",
        key=f"download_{selected_id}",
    )


def main() -> None:
    page = _sidebar()
    runs = _read_runs()
    if page == "Dashboard":
        dashboard_page(runs)
    elif page == "New research":
        new_research_page(runs)
    elif page == "Research history":
        history_page(runs)
    elif page == "Reports":
        reports_page(runs)


if __name__ == "__main__":
    main()
