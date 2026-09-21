
import os
import time

from dotenv import load_dotenv
from tavily import TavilyClient


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")

if not api_key:
    raise RuntimeError("TAVILY_API_KEY is not set")


# ============================================================
# TAVILY CLIENT
# ============================================================

client = TavilyClient(api_key=api_key)


# ============================================================
# SEARCH FUNCTION
# ============================================================

def search_web(
    query: str,
    max_results: int = 3,
    retries: int = 3
):
    """
    Search the web using Tavily.

    The function automatically retries temporary
    connection failures instead of crashing the
    complete research pipeline.
    """

    if not query or not query.strip():
        return []

    query = query.strip()

    for attempt in range(1, retries + 1):

        try:

            print(
                f"[Searcher] Searching: {query}"
            )

            response = client.search(
                query=query,
                search_depth="basic",
                max_results=max_results
            )

            results = response.get(
                "results",
                []
            )

            print(
                f"[Searcher] Found {len(results)} results"
            )

            return results

        except Exception as error:

            print(
                f"[Searcher] Attempt "
                f"{attempt}/{retries} failed: "
                f"{error}"
            )

            # ------------------------------------------------
            # If this was the final attempt, don't crash
            # the entire research pipeline.
            # ------------------------------------------------

            if attempt == retries:

                print(
                    "[Searcher] All retry attempts failed."
                )

                return []

            # ------------------------------------------------
            # Wait before retrying.
            #
            # 1st failure → 2 seconds
            # 2nd failure → 4 seconds
            # ------------------------------------------------

            wait_time = 2 ** attempt

            print(
                f"[Searcher] Retrying in "
                f"{wait_time} seconds..."
            )

            time.sleep(wait_time)