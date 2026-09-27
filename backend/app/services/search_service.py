import os
from pathlib import Path

from dotenv import load_dotenv
from tavily import TavilyClient

from app.services.source_ranker import rank_sources
from app.services.scholarly_search import search_scholarly


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

api_key = os.getenv(
    "TAVILY_API_KEY"
)

if not api_key:
    raise RuntimeError(
        "TAVILY_API_KEY is not set"
    )

client = TavilyClient(
    api_key=api_key
)


def search_web(
    query: str,
    max_results: int = 5
) -> list[dict]:

    all_results = []

    # Web search
    try:

        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results
        )

        for result in response.get(
            "results",
            []
        ):

            item = dict(result)

            item["source_type"] = (
                "Web Search"
            )

            all_results.append(
                item
            )

    except Exception as error:

        print(
            f"[Tavily] Error: {error}"
        )

    # Scholarly search
    scholarly_results = search_scholarly(
        query,
        limit=max_results
    )

    all_results.extend(
        scholarly_results
    )

    # Deduplicate
    unique = {}

    for item in all_results:

        url = item.get(
            "url",
            ""
        )

        doi = item.get(
            "doi",
            ""
        )

        title = item.get(
            "title",
            ""
        )

        key = (
            doi
            or url
            or title.lower()
        )

        if not key:
            continue

        existing = unique.get(
            key
        )

        if existing is None:

            unique[key] = item

        else:

            old_quality = existing.get(
                "source_quality",
                0
            )

            new_quality = item.get(
                "source_quality",
                0
            )

            if new_quality > old_quality:
                unique[key] = item

    ranked = rank_sources(
        list(
            unique.values()
        )
    )

    return ranked[
        : max_results * 2
    ]

