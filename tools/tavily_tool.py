from tavily import TavilyClient
from Settings import settings

class TavilySearchTool:
    def __init__(self):
        self.tavilyClient = TavilyClient(api_key=settings.TAVILY_API_KEY)

    def tavily_search(self, query: str, max_results: int = 5) -> str:
        response = self.tavilyClient.search(
            query=query,
            max_results=max_results,
        )

        results = []

        for i, r in enumerate(response["results"], 1):
            title = r.get("title", "Unknown")
            url = r.get("url", "")
            snippet = r.get("content", "").strip()

            # keep only first 300 chars to avoid wall of text

            if len(snippet) > 300:
                snippet = snippet[:300].rsplit(" ", 1)[0] + "..."

            results.append(
                f"""
                ### Result {i}
                **Title**: {title}\n
                URL: {url}\n
                snippet: {snippet}
                """
            )
        
        return '\n\n'.join(results)