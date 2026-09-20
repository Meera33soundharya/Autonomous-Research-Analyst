import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")

if not api_key:
    raise RuntimeError("TAVILY_API_KEY is not set")

client = TavilyClient(api_key=api_key)


def search_web(query: str):
    response = client.search(
        query=query,
        search_depth="basic",
        max_results=3
    )

    return response.get("results", [])