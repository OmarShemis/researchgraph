"""External research tools, constructed only when requested."""


def build_web_search():
    from langchain_tavily import TavilySearch

    return TavilySearch(max_results=5)
