import os
from typing import List, Dict, Any
from app.observability.logging import logger
from app.config import settings

class WebSearchTool:
    """
    Search tool to fetch information from the web when local RAG evidence is insufficient.
    """
    def __init__(self):
        self.tavily_api_key = getattr(settings, "TAVILY_API_KEY", None)

    async def search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        logger.info(f"Performing web search for: '{query}'")
        
        if self.tavily_api_key:
            try:
                from tavily import TavilyClient
                tavily = TavilyClient(api_key=self.tavily_api_key)
                response = tavily.search(query=query, search_depth="basic", max_results=max_results)
                
                results = []
                for res in response.get("results", []):
                    results.append({
                        "id": f"web-{hash(res['url'])}",
                        "text": res.get("content", ""),
                        "metadata": {
                            "source": res.get("url", ""),
                            "title": res.get("title", ""),
                            "source_type": "web"
                        },
                        "score": res.get("score", 0.5)
                    })
                return results
            except Exception as e:
                logger.error(f"Tavily search failed: {str(e)}")
        
        # Mock fallback for demonstration
        return [
            {
                "id": "web-mock-1",
                "text": f"Dữ liệu tìm kiếm web giả lập cho: {query}. Hệ thống phát hiện tài liệu nội bộ không đủ thông tin.",
                "metadata": {"source": "https://google.com", "title": "Web Search Fallback", "source_type": "web"},
                "score": 0.8
            }
        ]

web_search_tool = WebSearchTool()
