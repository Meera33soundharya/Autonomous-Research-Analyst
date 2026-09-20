from app.services.search_service import search_web


def run_search(questions: list[str]):
    results = []

    for question in questions:
        print(f"\nSearching: {question}")

        result = search_web(question)

        results.extend(result)

    return results