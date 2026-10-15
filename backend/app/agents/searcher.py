from concurrent.futures import ThreadPoolExecutor

from app.services.search_service import search_web
from app.services.query_expander import expand_search_queries


def _search_query(query: str) -> tuple[list[dict], list[dict]]:
    errors = []
    results = search_web(
        query,
        max_results=3,
        diagnostics=errors,
    )
    return results, errors


def run_search_with_diagnostics(
    topic: str,
    questions: list[str]
) -> tuple[list[dict], dict]:

    all_results = []
    source_indices = {}
    query_cache = {}
    diagnostics = {
        "search_query_count": 0,
        "errors": [],
        "by_question": [],
    }

    query_map = expand_search_queries(
        topic,
        questions,
        diagnostics["errors"],
    )

    for question in questions:

        queries = query_map.get(
            question,
            [
                question,
                f"{question} research study evidence"
            ]
        )

        question_queries = []
        print(
            f"\n[Searcher] Question: {question}"
        )

        seen_question_queries = set()
        for query in queries:
            query = str(query).strip()
            normalized_query = query.casefold()
            if not query or normalized_query in seen_question_queries:
                continue
            seen_question_queries.add(normalized_query)
            question_queries.append(query)
            print(f"\n[Searcher] Query: {query}")

        missing_queries = [
            query for query in question_queries if query not in query_cache
        ]
        if missing_queries:
            with ThreadPoolExecutor(
                max_workers=min(2, len(missing_queries))
            ) as executor:
                search_results = executor.map(_search_query, missing_queries)
                for query, (results, search_errors) in zip(
                    missing_queries,
                    search_results,
                ):
                    query_cache[query] = results
                    diagnostics["errors"].extend(
                        {
                            "question": question,
                            "query": query,
                            **error,
                        }
                        for error in search_errors
                    )

        for query in question_queries:
            results = query_cache[query]

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

                if key in source_indices:
                    existing = all_results[source_indices[key]]
                    if question not in existing["questions"]:
                        existing["questions"].append(question)
                    continue

                source_indices[key] = len(all_results)

                all_results.append(
                    {
                        "question": question,
                        "questions": [question],
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
                        ),
                        "source_identifier": (
                            result.get("doi")
                            or result.get("url")
                            or title
                        ),
                    }
                )

        diagnostics["search_query_count"] += len(question_queries)
        diagnostics["by_question"].append({
            "question": question,
            "search_queries": question_queries,
            "source_count": sum(
                question in source["questions"]
                for source in all_results
            ),
        })

    print(
        f"\n[Searcher] Total unique sources: "
        f"{len(all_results)}"
    )

    diagnostics["unique_source_count"] = len(all_results)
    return all_results, diagnostics


def run_search(
    topic: str,
    questions: list[str]
) -> list[dict]:
    results, _ = run_search_with_diagnostics(topic, questions)
    return results
