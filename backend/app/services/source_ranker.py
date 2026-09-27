from urllib.parse import urlparse


HIGH_TRUST_DOMAINS = {
    "ieee.org",
    "ieeexplore.ieee.org",
    "nature.com",
    "science.org",
    "sciencedirect.com",
    "springer.com",
    "acm.org",
    "nber.org",
    "nih.gov",
    "ncbi.nlm.nih.gov",
    "who.int",
    "nasa.gov",
    "gov",
    "edu",
}


LOW_TRUST_DOMAINS = {
    "medium.com",
    "youtube.com",
    "youtu.be",
    "scribd.com",
}


def get_domain(url: str) -> str:

    try:
        host = urlparse(
            url
        ).netloc.lower()

        return host.replace(
            "www.",
            ""
        ).split(":")[0]

    except Exception:
        return ""


def score_source(
    result: dict
) -> float:

    url = result.get(
        "url",
        ""
    )

    source_type = result.get(
        "source_type",
        ""
    )

    title = result.get(
        "title",
        ""
    ).lower()

    domain = get_domain(
        url
    )

    score = 0.45

    if source_type == "IEEE Xplore":
        score = 0.98

    elif source_type == "Crossref Scholarly":
        score = 0.90

    elif source_type == "Semantic Scholar":
        score = 0.88

    elif domain in HIGH_TRUST_DOMAINS:
        score = 0.94

    elif domain.endswith(".gov"):
        score = 0.93

    elif domain.endswith(".edu"):
        score = 0.90

    elif domain in LOW_TRUST_DOMAINS:
        score = 0.20

    elif domain.endswith(".org"):
        score = 0.70

    elif domain.endswith(".com"):
        score = 0.50

    quality_terms = [
        "systematic review",
        "meta-analysis",
        "journal",
        "research",
        "study",
        "conference",
        "review",
        "official report",
    ]

    if any(
        term in title
        for term in quality_terms
    ):
        score += 0.04

    return max(
        0.0,
        min(score, 1.0)
    )


def rank_sources(
    results: list[dict]
) -> list[dict]:

    ranked = []

    for result in results:

        item = dict(result)

        item["source_quality"] = round(
            score_source(item),
            2
        )

        ranked.append(
            item
        )

    ranked.sort(
        key=lambda item: (
            item.get(
                "source_quality",
                0
            ),
            item.get(
                "citation_count",
                0
            ),
            item.get(
                "score",
                0
            )
        ),
        reverse=True
    )

    return ranked
