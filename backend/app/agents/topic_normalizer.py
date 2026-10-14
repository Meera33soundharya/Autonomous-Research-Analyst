import re


_META_START = re.compile(
    r"(?i)(?<=[.!?])\s+(?="
    r"this is (?:a )?(?:good )?test\b|"
    r"this makes it (?:a )?(?:good )?test\b|"
    r"it(?:'s| is) (?:also )?(?:a )?(?:good )?test\b|"
    r"which makes (?:it|this)\b|"
    r"accuracy (?:of\b|matters more\b)|"
    r"this is a test of\b|"
    r"test whether\b|"
    r"meta(?:-commentary)?\s*:"
    r")"
)
_TOPIC_SECTION = re.compile(
    r"(?ims)\A\s*(?:RESEARCH\s+)?TOPIC\s*:\s*(.+?)"
    r"(?=^\s*(?:SCOPE|META|INSTRUCTIONS|ROLE)\s*:|\Z)"
)
_SCOPE_SECTION = re.compile(r"(?ims)^\s*SCOPE\s*:\s*(.+?)(?=^\s*[A-Z][A-Z _-]*\s*:|\Z)")
_META_SECTION = re.compile(r"(?ims)^\s*META\s*:\s*(.+?)(?=^\s*[A-Z][A-Z _-]*\s*:|\Z)")
_TITLE_AND_SCOPE = re.compile(
    r"(?ims)\A\s*([^\r\n]+)\s*\r?\n\s*SCOPE\s*:\s*(.+?)"
    r"(?=^\s*[A-Z][A-Z _-]*\s*:|\Z)"
)


def normalize_research_topic(raw_topic: str) -> dict[str, str]:
    """Separate a clearly labeled topic or explicit evaluation meta-text."""
    raw = (raw_topic or "").strip()
    topic_match = _TOPIC_SECTION.search(raw)

    if topic_match:
        topic = topic_match.group(1).strip()
        scope_match = _SCOPE_SECTION.search(raw)
        scope = scope_match.group(1).strip() if scope_match else ""
        meta_match = _META_SECTION.search(raw)
        meta = meta_match.group(1).strip() if meta_match else ""
    else:
        scope_match = _TITLE_AND_SCOPE.search(raw)
        if scope_match:
            topic = scope_match.group(1).strip()
            scope = scope_match.group(2).strip()
            meta = ""
        else:
            scope = ""
            meta_match = _META_START.search(raw)
            prompt_markers = (
                "step 0 - parse the request",
                "you are a research analyst producing a fact-checked report",
            )
            if any(marker in raw[:1000].lower() for marker in prompt_markers):
                topic = ""
                meta = raw
            else:
                topic = raw[:meta_match.start()].strip() if meta_match else raw
                meta = raw[meta_match.end():].strip() if meta_match else ""

    return {
        "topic": topic,
        "scope": scope,
        "meta": meta,
        "raw_topic": raw,
    }
