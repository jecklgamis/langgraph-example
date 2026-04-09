from ddgs import DDGS


def search_web(query: str) -> str:
    """Performs a web search and returns the top results."""
    print("Let me do some web searching for that")
    try:
        results = DDGS().text(query, max_results=10)
        if not results:
            return "No results found."
        return "\n\n".join(
            f"{r['title']}\n{r['href']}\n{r['body']}" for r in results
        )
    except Exception as e:
        return f"Search failed: {e}"
