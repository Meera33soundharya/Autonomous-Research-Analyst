from datetime import date, datetime, timedelta
from html import escape
from typing import Any


AGENTS = (
    ("planner", "Planner", "Creates focused research questions"),
    ("searcher", "Searcher", "Collects relevant web sources"),
    ("researcher", "Researcher", "Extracts evidence-backed claims"),
    ("evidence_cleaner", "Evidence Cleaner", "Cleans and deduplicates claims"),
    ("citation_checker", "Citation Checker", "Checks claims against sources"),
    ("writer", "Writer", "Produces the final research report"),
)

AGENT_KEYS = tuple(agent[0] for agent in AGENTS)

DOCUMENT_STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{color-scheme:dark;font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
*{box-sizing:border-box}
html,body{margin:0;width:100%;background:transparent;color:#e8eefc;font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
body{font-size:13px;line-height:1.5}
.panel{background:#131b30;border:1px solid #242f4d;border-radius:12px;padding:18px}
.panel-title{font-size:14px;font-weight:700;color:#e8eefc}
.panel-subtitle{font-size:12px;color:#a8b4cf;margin-top:2px}
.grid-4{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}
.grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:16px}
.kpi{min-width:0}
.kpi-label{font-size:12px;color:#a8b4cf}
.kpi-value{font-size:28px;line-height:1.2;font-weight:700;letter-spacing:-.03em;margin-top:8px}
.kpi-foot{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:8px;color:#a8b4cf;font-size:11px}
.spark{width:76px;height:24px;flex:none}
.chart{width:100%;height:auto;display:block;margin-top:10px;overflow:visible}
.chart text{fill:#a8b4cf;font-size:11px;font-family:inherit}
.chart .gridline{stroke:#242f4d;stroke-width:1}
.chart .bar{fill:#6b8cff}
.chart .bar-last{fill:#87a0ff}
.agents{display:grid;gap:0;margin-top:10px}
.agent{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:center;padding:12px 0;border-top:1px solid #242f4d}
.agent:first-child{border-top:0}
.agent-name{font-size:12px;font-weight:650;color:#e8eefc}
.agent-detail{font-size:11px;color:#a8b4cf;margin-top:2px}
.pill{display:inline-flex;align-items:center;white-space:nowrap;border-radius:999px;border:1px solid #52617f;padding:3px 9px;font-size:10px;font-weight:700;color:#c4cde0;background:#202b43}
.pill.Completed{color:#3ddc97;border-color:#287e63;background:#143629}
.pill.Running{color:#9db2ff;border-color:#465b9a;background:#202c53}
.pill.Failed{color:#ff8da0;border-color:#a3495c;background:#442330}
.pill.Waiting{color:#b8c2d8;border-color:#52617f;background:#202b43}
.table-wrap{width:100%;overflow-x:auto;margin-top:14px}
table{width:100%;min-width:680px;border-collapse:collapse;text-align:left}
th{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:#a8b4cf;font-weight:650;padding:9px 10px;border-bottom:1px solid #34405d}
td{font-size:11px;color:#e8eefc;padding:11px 10px;border-bottom:1px solid #242f4d;white-space:nowrap}
td.topic{white-space:normal;min-width:140px;max-width:280px}
.muted{color:#a8b4cf}
.empty{border:1px dashed #52617f;border-radius:10px;padding:20px;text-align:center;color:#b8c2d8;margin-top:14px}
.donut-row{display:flex;align-items:center;gap:24px;margin-top:18px;min-height:160px}
.donut{width:144px;height:144px;flex:none;border-radius:50%;display:grid;place-items:center;position:relative}
.donut:after{content:"";position:absolute;inset:17px;background:#131b30;border-radius:50%}
.donut-center{z-index:1;text-align:center}
.donut-center strong{display:block;color:#e8eefc;font-size:22px}
.donut-center span{font-size:10px;color:#b8c2d8}
.legend{display:grid;gap:10px}
.legend-item{display:grid;grid-template-columns:9px minmax(70px,1fr) auto;gap:8px;align-items:center;color:#b8c2d8;font-size:11px}
.dot{width:8px;height:8px;border-radius:50%}
.supported{background:#3ddc97}
.partial{background:#ffb938}
.unsupported{background:#ff6b85}
.error{border:1px solid #a3495c;background:#301c2a;border-radius:12px;padding:16px 18px;color:#ffd7de;white-space:pre-wrap;overflow-wrap:anywhere}
.error-title{font-weight:750;color:#ff8da0;margin-bottom:5px}
.live-topic{font-size:16px;font-weight:700;color:#e8eefc}
.live-caption{font-size:12px;color:#b8c2d8;margin-top:4px}
:focus-visible{outline:3px solid #9db2ff;outline-offset:3px}
@media(max-width:900px){.grid-4{grid-template-columns:repeat(2,minmax(0,1fr))}.grid-2{grid-template-columns:1fr}}
@media(max-width:520px){.grid-4{grid-template-columns:1fr}.panel{padding:14px}.donut-row{gap:14px;flex-wrap:wrap}}
</style>
"""


def _document(content: str) -> str:
    return f"<!doctype html><html><head>{DOCUMENT_STYLE}</head><body>{content}</body></html>"


def _safe(value: Any) -> str:
    return escape(str(value if value is not None else ""), quote=True)


def _get(run: dict[str, Any], key: str, fallback: Any = None) -> Any:
    value = run.get(key, fallback)
    return fallback if value is None else value


def _parse_date(run: dict[str, Any]) -> date | None:
    value = run.get("created") or run.get("date")
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except (TypeError, ValueError):
        return None


def _relative_date(run: dict[str, Any]) -> str:
    created = _parse_date(run)
    if created is None:
        return "Date unavailable"
    days = (date.today() - created).days
    if days <= 0:
        return "Today"
    if days == 1:
        return "Yesterday"
    return f"{days} days ago"


def get_questions(state: dict[str, Any]) -> list[str]:
    questions = state.get("research_questions") or state.get("questions") or []
    return [str(question) for question in questions if question is not None]


def get_sources(state: dict[str, Any]) -> list[dict[str, Any]]:
    sources = state.get("search_results") or state.get("sources") or []
    return [source for source in sources if isinstance(source, dict)]


def get_claims(state: dict[str, Any]) -> list[dict[str, Any]]:
    claims = state.get("claims") or []
    if claims:
        return [claim for claim in claims if isinstance(claim, dict)]
    flattened: list[dict[str, Any]] = []
    for group in state.get("verified_evidence") or []:
        if isinstance(group, dict):
            flattened.extend(
                finding
                for finding in group.get("findings", [])
                if isinstance(finding, dict)
            )
    return flattened


def get_verdict(claim: dict[str, Any]) -> str:
    raw = str(claim.get("status") or claim.get("verdict") or "").strip().lower()
    if raw in {"supported", "supported."}:
        return "Supported"
    if raw in {
        "partial",
        "partially_supported",
        "partially supported",
        "partially_supported.",
    }:
        return "Partial"
    if raw in {"unsupported", "unsupported."}:
        return "Unsupported"
    return "Unverified"


def count_verdicts(claims: list[dict[str, Any]]) -> tuple[int, int, int]:
    supported = sum(get_verdict(claim) == "Supported" for claim in claims)
    partial = sum(get_verdict(claim) == "Partial" for claim in claims)
    unsupported = sum(get_verdict(claim) == "Unsupported" for claim in claims)
    return supported, partial, unsupported


def claims_table_rows(claims: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "Claim": str(claim.get("claim") or claim.get("finding") or ""),
            "Status": get_verdict(claim),
            "Source": str(claim.get("source_title") or claim.get("source") or ""),
            "Source URL": str(claim.get("source_url") or ""),
        }
        for claim in claims
    ]


def sources_table_rows(sources: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "Title": str(source.get("title") or "Untitled source"),
            "URL": str(source.get("url") or ""),
            "Type": str(source.get("source_type") or ""),
            "Year": str(source.get("year") or ""),
        }
        for source in sources
    ]


def _status_class(status: Any) -> str:
    normalized = str(status or "Waiting").title()
    return normalized if normalized in {"Waiting", "Running", "Completed", "Failed"} else "Waiting"


def _agent_rows(statuses: dict[str, str]) -> str:
    rows: list[str] = []
    for key, name, description in AGENTS:
        status = _status_class(statuses.get(key, "Waiting"))
        rows.append(
            f'<div class="agent"><div><div class="agent-name">{_safe(name)}</div>'
            f'<div class="agent-detail">{_safe(description)}</div></div>'
            f'<span class="pill {status}" aria-label="Status: {status}">{status}</span></div>'
        )
    return "".join(rows)


def agent_panel_html(
    statuses: dict[str, str],
    title: str = "Active pipeline",
    subtitle: str = "Live agent status",
) -> str:
    content = (
        '<section class="panel"><div class="panel-title">'
        f"{_safe(title)}</div><div class=\"panel-subtitle\">{_safe(subtitle)}</div>"
        f'<div class="agents">{_agent_rows(statuses)}</div></section>'
    )
    return _document(content)


def error_card_html(message: str, title: str = "Research run failed") -> str:
    content = (
        '<section class="error" role="alert"><div class="error-title">'
        f"{_safe(title)}</div><div>{_safe(message)}</div></section>"
    )
    return _document(content)


def empty_state_html(title: str, description: str) -> str:
    content = (
        f'<div class="empty"><strong>{_safe(title)}</strong>'
        f'<div class="muted">{_safe(description)}</div></div>'
    )
    return _document(content)


def live_header_html(topic: str, stage: str, elapsed_seconds: float) -> str:
    content = (
        '<section class="panel"><div class="live-topic">'
        f"{_safe(topic)}</div><div class=\"live-caption\">"
        f"Running · {_safe(stage)} · {elapsed_seconds:.1f}s elapsed</div></section>"
    )
    return _document(content)


def _sparkline(values: list[float], color: str = "#6b8cff") -> str:
    if not values:
        return ""
    width, height = 76, 24
    low, high = min(values), max(values)
    spread = high - low or 1
    points = []
    for index, value in enumerate(values):
        x = 2 + index * (width - 4) / max(1, len(values) - 1)
        y = height - 3 - ((value - low) / spread) * (height - 7)
        points.append(f"{x:.1f},{y:.1f}")
    return (
        f'<svg class="spark" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Seven day trend"><polyline fill="none" stroke="{color}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'points="{" ".join(points)}"/></svg>'
    )


def _trend_values(runs: list[dict[str, Any]], measure: str) -> list[float]:
    days = [date.today() - timedelta(days=6 - index) for index in range(7)]
    values: list[float] = []
    for day in days:
        matching = [run for run in runs if _parse_date(run) == day]
        if measure == "reports":
            values.append(float(sum(bool(run.get("report")) for run in matching)))
        elif measure == "sources":
            values.append(float(sum(int(run.get("n_sources", 0) or 0) for run in matching)))
        elif measure == "claims":
            values.append(
                float(
                    sum(
                        int(run.get("supported", 0) or 0)
                        + int(run.get("partial", 0) or 0)
                        + int(run.get("unsupported", 0) or 0)
                        for run in matching
                    )
                )
            )
        else:
            accuracies = [
                float(run["accuracy"])
                for run in matching
                if run.get("accuracy") is not None
            ]
            values.append(sum(accuracies) / len(accuracies) if accuracies else 0.0)
    return values


def _runs_chart(runs: list[dict[str, Any]]) -> str:
    days = [date.today() - timedelta(days=6 - index) for index in range(7)]
    counts = [
        sum(_parse_date(run) == day for run in runs)
        for day in days
    ]
    maximum = max(counts, default=0)
    top = max(1, maximum)
    chart_width, chart_height = 560, 190
    left, right, baseline, chart_top = 38, 548, 145, 18
    chart_range = baseline - chart_top
    grid_values = sorted({0, (top + 1) // 2, top})
    grid = "".join(
        f'<line class="gridline" x1="{left}" x2="{right}" y1="{baseline - value / top * chart_range:.1f}" '
        f'y2="{baseline - value / top * chart_range:.1f}"/>'
        f'<text x="{left - 8}" y="{baseline - value / top * chart_range + 4:.1f}" text-anchor="end">{value}</text>'
        for value in grid_values
    )
    bars: list[str] = []
    slot = (right - left) / len(days)
    bar_width = min(42, slot * 0.58)
    for index, (day, count) in enumerate(zip(days, counts)):
        height = count / top * chart_range if count else 0
        x = left + index * slot + (slot - bar_width) / 2
        y = baseline - height
        cls = "bar-last" if index == len(days) - 1 else "bar"
        bars.append(
            f'<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" '
            f'height="{max(0, height):.1f}" rx="5"><title>{count} runs on '
            f'{day.isoformat()}</title></rect>'
            f'<text x="{x + bar_width / 2:.1f}" y="169" text-anchor="middle">'
            f'{_safe(day.strftime("%a"))}</text>'
        )
    return (
        f'<svg class="chart" viewBox="0 0 {chart_width} {chart_height}" role="img" '
        f'aria-label="Research runs per day for the last seven days">'
        f"{grid}{''.join(bars)}</svg>"
    )


def _run_status(run: dict[str, Any]) -> str:
    return _status_class(run.get("status", "Completed"))


def _recent_table(runs: list[dict[str, Any]]) -> str:
    if not runs:
        return (
            '<div class="empty"><strong>No research runs yet</strong>'
            '<div class="muted">Start a research run to see activity here.</div></div>'
        )
    rows: list[str] = []
    for run in runs[:8]:
        accuracy = run.get("accuracy")
        accuracy_text = f"{_safe(accuracy)}%" if accuracy is not None else "—"
        status = _run_status(run)
        duration = float(run.get("seconds", 0) or 0)
        rows.append(
            "<tr>"
            f'<td class="topic">{_safe(run.get("topic", "Research"))}</td>'
            f'<td><span class="pill {status}">{status}</span></td>'
            f'<td>{int(run.get("n_sources", 0) or 0)}</td>'
            f'<td>{int(run.get("n_claims", 0) or 0)}</td>'
            f"<td>{accuracy_text}</td>"
            f"<td>{duration:.1f}s</td>"
            f"<td>{_safe(_relative_date(run))}</td>"
            "</tr>"
        )
    return (
        '<div class="table-wrap"><table><thead><tr><th>Topic</th><th>Status</th>'
        "<th>Sources</th><th>Claims</th><th>Accuracy</th><th>Duration</th><th>Date</th>"
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
    )


def _donut(supported: int, partial: int, unsupported: int) -> str:
    total = supported + partial + unsupported
    if total:
        supported_end = supported / total * 100
        partial_end = supported_end + partial / total * 100
        ring = (
            "conic-gradient(#3ddc97 0 "
            f"{supported_end:.3f}%,#ffb938 {supported_end:.3f}% "
            f"{partial_end:.3f}%,#ff6b85 {partial_end:.3f}% 100%)"
        )
        center = f"{round(supported_end)}%"
        detail = "supported"
    else:
        ring = "#242f4d"
        center = "—"
        detail = "no claims"
    return (
        '<div class="donut-row"><div class="donut" role="img" '
        f'aria-label="Claim verification: {supported} supported, {partial} partial, '
        f'{unsupported} unsupported" style="background:{ring}">'
        f'<div class="donut-center"><strong>{center}</strong><span>{detail}</span></div></div>'
        '<div class="legend">'
        f'<div class="legend-item"><span class="dot supported"></span><span>Supported</span><strong>{supported}</strong></div>'
        f'<div class="legend-item"><span class="dot partial"></span><span>Partial</span><strong>{partial}</strong></div>'
        f'<div class="legend-item"><span class="dot unsupported"></span><span>Unsupported</span><strong>{unsupported}</strong></div>'
        "</div></div>"
    )


def dashboard_html(
    runs: list[dict[str, Any]],
    active_statuses: dict[str, str] | None = None,
) -> str:
    active_statuses = active_statuses or {}
    completed_runs = [run for run in runs if run.get("status") != "Failed"]
    reports = sum(bool(run.get("report")) for run in runs)
    sources = sum(int(run.get("n_sources", 0) or 0) for run in completed_runs)
    supported = sum(int(run.get("supported", 0) or 0) for run in completed_runs)
    partial = sum(int(run.get("partial", 0) or 0) for run in completed_runs)
    unsupported = sum(int(run.get("unsupported", 0) or 0) for run in completed_runs)
    verified = supported + partial + unsupported
    accuracy = f"{round(100 * supported / verified)}%" if verified else "—"

    cards = (
        ("Reports generated", str(reports), "reports", f"{reports} saved reports"),
        ("Sources collected", str(sources), "sources", f"{sources} sources in completed runs"),
        ("Claims verified", str(verified), "claims", f"{verified} claims with a verdict"),
        ("Citation accuracy", accuracy, "accuracy", "Supported share of verified claims"),
    )
    kpi_markup: list[str] = []
    for label, value, metric, note in cards:
        kpi_markup.append(
            f'<section class="panel kpi"><div class="kpi-label">{_safe(label)}</div>'
            f'<div class="kpi-value">{_safe(value)}</div><div class="kpi-foot">'
            f'<span>{_safe(note)}</span>{_sparkline(_trend_values(runs, metric))}</div></section>'
        )

    if not active_statuses:
        active_statuses = runs[0].get("agents", {}) if runs else {}
    if not active_statuses:
        active_statuses = {key: "Waiting" for key in AGENT_KEYS}

    content = (
        f'<div class="grid-4">{"".join(kpi_markup)}</div>'
        '<div class="grid-2"><section class="panel"><div class="panel-title">Research runs per day</div>'
        '<div class="panel-subtitle">Last seven days</div>'
        f'{_runs_chart(runs)}</section>'
        '<section class="panel"><div class="panel-title">Active pipeline</div>'
        '<div class="panel-subtitle">Most recent run</div>'
        f'<div class="agents">{_agent_rows(active_statuses)}</div></section></div>'
        '<div class="grid-2"><section class="panel"><div class="panel-title">Recent research</div>'
        '<div class="panel-subtitle">Latest saved runs</div>'
        f'{_recent_table(runs)}</section>'
        '<section class="panel"><div class="panel-title">Claim verification</div>'
        '<div class="panel-subtitle">Completed runs</div>'
        f'{_donut(supported, partial, unsupported)}</section></div>'
    )
    return _document(content)
