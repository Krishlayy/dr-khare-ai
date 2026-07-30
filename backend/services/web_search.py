import httpx

from backend.core.logging_config import get_logger
from backend.core.config import settings
from backend.core.http_client import get_client

logger = get_logger("services.web_search")

async def search_web(query: str, max_results: int = 5) -> tuple[str, list[dict]]:
    """
    Search the web via Tavily API.
    Returns (context_text, sources_list).
    """
    if not settings.TAVILY_API_KEY:
        logger.error("TAVILY_API_KEY not set")
        return "", []

    try:
        client = get_client()
        resp = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "include_answer": False,
                "max_results": max_results,
            },
        )
        resp.raise_for_status()
        data = resp.json()

        snippets: list[str] = []
        sources: list[dict] = []

        for item in data.get("results", []):
            snippet = item.get("content", "")
            if not snippet:
                continue
            snippets.append(snippet)
            sources.append(
                {
                    "title": item.get("title") or "Web Search Result",
                    "url": item.get("url", ""),
                    "snippet": snippet[:300],
                }
            )

        if not snippets:
            logger.info("Tavily returned no results for: %s", query[:80])
            return "", []

        context = "\n\n".join(s for s in snippets[:max_results] if s.strip())
        logger.info(
            "Web search: %d snippets found for query: %s",
            len(sources),
            query[:80],
        )
        return context, sources[:max_results]

    except Exception as exc:
        logger.error("Web search failed: %s", exc)
        return "", []
