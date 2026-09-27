import os
import re
import requests

from dotenv import load_dotenv

load_dotenv()

CROSSREF_URL = "https://api.crossref.org/v1/works"
SEMANTIC_SCHOLAR_URL = (
    "https://api.semanticscholar.org/graph/v1/paper/search"
)
IEEE_URL = "https://ieeexploreapi.ieee.org/api/v1/search/articles"


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def search_crossref(
    query: str,
    limit: int = 5
) -> list[dict]:

    try:

        response = requests.get(
            CROSSREF_URL,
            params={
                "query.bibliographic": query,
                "rows": limit,
                "select": (
                    "DOI,title,author,published,container-title,"
                    "URL,type,abstract,is-referenced-by-count"
                ),
                "mailto": os.getenv(
                    "CROSSREF_EMAIL",
                    ""
                )
            },
            headers={
                "User-Agent": (
                    "AutonomousResearchAnalyst/1.0 "
                    "(research application)"
                )
            },
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for item in data.get(
            "message",
            {}
        ).get(
            "items",
            []
        ):

            title_list = item.get(
                "title",
                []
            )

            title = (
                title_list[0]
                if title_list
                else ""
            )

            doi = item.get(
                "DOI",
                ""
            )

            authors = []

            for author in item.get(
                "author",
                []
            ):

                name = " ".join(
                    part
                    for part in [
                        author.get("given", ""),
                        author.get("family", "")
                    ]
                    if part
                )

                if name:
                    authors.append(name)

            published = item.get(
                "published",
                {}
            ).get(
                "date-parts",
                [[]]
            )[0]

            year = (
                str(published[0])
                if published
                else ""
            )

            venue_list = item.get(
                "container-title",
                []
            )

            venue = (
                venue_list[0]
                if venue_list
                else ""
            )

            url = item.get(
                "URL",
                ""
            )

            abstract = clean_text(
                item.get(
                    "abstract",
                    ""
                )
            )

            results.append(
                {
                    "title": title,
                    "url": url,
                    "content": abstract,
                    "abstract": abstract,
                    "authors": authors,
                    "year": year,
                    "venue": venue,
                    "doi": doi,
                    "citation_count": item.get(
                        "is-referenced-by-count",
                        0
                    ),
                    "source_type": "Crossref Scholarly",
                    "publication_type": item.get(
                        "type",
                        ""
                    )
                }
            )

        return results

    except Exception as error:

        print(
            f"[Crossref] Error: {error}"
        )

        return []


def search_semantic_scholar(
    query: str,
    limit: int = 5
) -> list[dict]:

    try:

        headers = {}

        api_key = os.getenv(
            "SEMANTIC_SCHOLAR_API_KEY"
        )

        if api_key:
            headers["x-api-key"] = api_key

        response = requests.get(
            SEMANTIC_SCHOLAR_URL,
            params={
                "query": query,
                "limit": limit,
                "fields": (
                    "title,abstract,url,year,authors,"
                    "venue,citationCount,externalIds,"
                    "openAccessPdf,publicationTypes"
                )
            },
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for item in data.get(
            "data",
            []
        ):

            authors = [
                author.get(
                    "name",
                    ""
                )
                for author in item.get(
                    "authors",
                    []
                )
                if author.get(
                    "name"
                )
            ]

            external_ids = item.get(
                "externalIds",
                {}
            ) or {}

            doi = external_ids.get(
                "DOI",
                ""
            )

            abstract = clean_text(
                item.get(
                    "abstract",
                    ""
                )
            )

            results.append(
                {
                    "title": item.get(
                        "title",
                        ""
                    ),
                    "url": item.get(
                        "url",
                        ""
                    ),
                    "content": abstract,
                    "abstract": abstract,
                    "authors": authors,
                    "year": str(
                        item.get(
                            "year",
                            ""
                        )
                    ),
                    "venue": item.get(
                        "venue",
                        ""
                    ),
                    "doi": doi,
                    "citation_count": item.get(
                        "citationCount",
                        0
                    ),
                    "source_type": (
                        "Semantic Scholar"
                    ),
                    "publication_type": ",".join(
                        item.get(
                            "publicationTypes",
                            []
                        ) or []
                    )
                }
            )

        return results

    except Exception as error:

        print(
            f"[Semantic Scholar] Error: {error}"
        )

        return []


def search_ieee(
    query: str,
    limit: int = 5
) -> list[dict]:

    api_key = os.getenv(
        "IEEE_XPLORE_API_KEY"
    )

    if not api_key:
        return []

    try:

        response = requests.get(
            IEEE_URL,
            params={
                "querytext": query,
                "max_records": limit,
                "apikey": api_key
            },
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for article in data.get(
            "articles",
            []
        ):

            authors = []

            for author in article.get(
                "authors",
                {}
            ).get(
                "authors",
                []
            ):

                name = (
                    author.get(
                        "full_name",
                        ""
                    )
                )

                if name:
                    authors.append(name)

            abstract = clean_text(
                article.get(
                    "abstract",
                    ""
                )
            )

            results.append(
                {
                    "title": article.get(
                        "title",
                        ""
                    ),
                    "url": article.get(
                        "html_url",
                        ""
                    ),
                    "content": abstract,
                    "abstract": abstract,
                    "authors": authors,
                    "year": str(
                        article.get(
                            "publication_year",
                            ""
                        )
                    ),
                    "venue": article.get(
                        "publication_title",
                        ""
                    ),
                    "doi": article.get(
                        "doi",
                        ""
                    ),
                    "citation_count": 0,
                    "source_type": "IEEE Xplore",
                    "publication_type": article.get(
                        "content_type",
                        ""
                    )
                }
            )

        return results

    except Exception as error:

        print(
            f"[IEEE] Error: {error}"
        )

        return []


def search_scholarly(
    query: str,
    limit: int = 5
) -> list[dict]:

    results = []

    results.extend(
        search_ieee(
            query,
            limit
        )
    )

    results.extend(
        search_semantic_scholar(
            query,
            limit
        )
    )

    results.extend(
        search_crossref(
            query,
            limit
        )
    )

    unique = {}
    for result in results:

        key = (
            result.get("doi")
            or result.get("url")
            or result.get("title", "").lower()
        )

        if key:
            unique[key] = result

    return list(
        unique.values()
    )
