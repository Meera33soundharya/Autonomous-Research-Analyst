from app.services.search_service import search_web
from app.services.query_expander import expand_search_queries


def run_search(
    topic: str,
    questions: list[str]
) -> list[dict]:

    all_results = []
    seen_urls = set()

    query_map = expand_search_queries(
        topic,
        questions
    )

    for question in questions:

        queries = query_map.get(
            question,
            [
                question,
                f"{question} research study evidence"
            ]
        )

        print(
            f"\n[Searcher] Question: {question}"
        )

        for query in queries:

            print(
                f"[Searcher] Query: {query}"
            )

            results = search_web(
                query,
                max_results=3
            )

            for result in results:

                url = result.get(
                    "url",
                    ""
                )

                title = result.get(
                    "title",
                    ""
                )

                key = (
                    url
                    or title.lower()
                )

                if not key:
                    continue

                if key in seen_urls:
                    continue

                seen_urls.add(key)

                all_results.append(
                    {
                        "question": question,
                        "search_query": query,
                        "title": title,
                        "url": url,
                        "content": result.get(
                            "content",
                            ""
                        ),
                        "abstract": result.get(
                            "abstract",
                            ""
                        ),
                        "authors": result.get(
                            "authors",
                            []
                        ),
                        "year": result.get(
                            "year",
                            ""
                        ),
                        "venue": result.get(
                            "venue",
                            ""
                        ),
                        "doi": result.get(
                            "doi",
                            ""
                        ),
                        "citation_count": result.get(
                            "citation_count",
                            0
                        ),
                        "source_type": result.get(
                            "source_type",
                            "Web Search"
                        ),
                        "source_quality": result.get(
                            "source_quality",
                            0
                        )
                    }
                )

    print(
        f"\n[Searcher] Total unique sources: "
        f"{len(all_results)}"
    )

    return all_results



