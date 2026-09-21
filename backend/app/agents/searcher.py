from app.services.search_service import search_web


def run_search(questions: list[str]) -> list[dict]:

    all_results = []

    for question in questions:

        results = search_web(question)

        for result in results:

            all_results.append({
                "question": question,
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", "")
            })

    return all_results