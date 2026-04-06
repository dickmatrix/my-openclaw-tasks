#!/usr/bin/env python3
"""
Google Gemini Grounding 搜索 Skill - 高配免费额度
每日 1,000 次免费 Google 搜索增强（需要 Gemini API Key）
"""
import asyncio
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
except ImportError:
    logger.warning("google-generativeai not installed. Install with: pip install google-generativeai")
    genai = None


@dataclass
class SearchResult:
    """搜索结果数据结构"""
    title: str
    url: str
    snippet: str
    source: str = "Google (via Gemini)"
    relevance_score: float = 0.95


class GeminiGroundingSearchTool:
    """Google Gemini Grounding 搜索工具 - 高配免费额度"""
    
    def __init__(self, api_key: str):
        if genai is None:
            raise ImportError("google-generativeai package required. Install: pip install google-generativeai")
        
        self.name = "gemini_grounding_search"
        self.description = "通过 Google Gemini 执行 Google 搜索增强（每日 1,000 次免费）"
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
    
    def execute(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """执行 Gemini Grounding 搜索
        
        Args:
            query: 搜索关键词
            top_k: 返回结果数量
            
        Returns:
            List[SearchResult]: 搜索结果列表
        """
        if not self.validate_query(query):
            return []
        
        try:
            # 使用 Gemini 的 Google Search Grounding
            response = self.model.generate_content(
                f"Search for: {query}\n\nProvide top {top_k} results with title, URL, and snippet.",
                tools=[genai.Tool(google_search=genai.GoogleSearch())]
            )
            
            results = []
            
            # 解析 Gemini 返回的搜索结果
            if response.text:
                # 从响应中提取搜索结果（Gemini 会返回格式化的搜索结果）
                lines = response.text.split('\n')
                for idx, line in enumerate(lines[:top_k]):
                    if line.strip():
                        # 简单解析：假设格式为 "标题 | URL | 摘要"
                        parts = line.split('|')
                        if len(parts) >= 2:
                            results.append(SearchResult(
                                title=parts[0].strip() if len(parts) > 0 else "",
                                url=parts[1].strip() if len(parts) > 1 else "",
                                snippet=parts[2].strip() if len(parts) > 2 else "",
                                source="Google (via Gemini)",
                                relevance_score=1.0 - (idx * 0.05)
                            ))
            
            logger.info(f"Gemini Grounding search for '{query}' returned {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"Gemini Grounding search error: {e}")
            return []
    
    def execute_batch(self, queries: List[str], top_k: int = 10) -> Dict[str, List[SearchResult]]:
        """执行多个搜索查询
        
        Args:
            queries: 搜索关键词列表
            top_k: 每个查询返回结果数量
            
        Returns:
            Dict[str, List[SearchResult]]: 查询结果映射
        """
        output = {}
        for query in queries:
            try:
                output[query] = self.execute(query, top_k)
            except Exception as e:
                logger.error(f"Error searching for '{query}': {e}")
                output[query] = []
        
        return output
    
    def validate_query(self, query: str) -> bool:
        """验证搜索查询有效性"""
        if not query or len(query.strip()) < 2:
            return False
        if len(query) > 500:
            return False
        return True


def search_gemini(query: str, api_key: Optional[str] = None, top_k: int = 10, **kwargs) -> Dict:
    """Gemini Grounding 搜索主函数"""
    if not api_key:
        api_key = kwargs.get("GEMINI_API_KEY") or kwargs.get("gemini_api_key")
    
    if not api_key:
        return {
            "status": "error",
            "message": "Gemini API Key required",
            "solution": "Set GEMINI_API_KEY environment variable or pass api_key parameter"
        }
    
    try:
        tool = GeminiGroundingSearchTool(api_key=api_key)
    except ImportError as e:
        return {
            "status": "error",
            "message": f"Gemini tool not available: {e}",
            "solution": "pip install google-generativeai"
        }
    
    if not tool.validate_query(query):
        return {"status": "error", "message": "Invalid query"}
    
    results = tool.execute(query, top_k=top_k)
    
    return {
        "status": "success",
        "provider": "Google Gemini Grounding (1000 free/day)",
        "query": query,
        "count": len(results),
        "results": [
            {
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "source": r.source,
                "confidence": f"{r.relevance_score * 100:.1f}%"
            }
            for r in results
        ]
    }


def search_batch_gemini(queries: List[str], api_key: Optional[str] = None, top_k: int = 10, **kwargs) -> Dict:
    """Gemini Grounding 批量搜索"""
    if not api_key:
        api_key = kwargs.get("GEMINI_API_KEY") or kwargs.get("gemini_api_key")
    
    if not api_key:
        return {
            "status": "error",
            "message": "Gemini API Key required"
        }
    
    try:
        tool = GeminiGroundingSearchTool(api_key=api_key)
    except ImportError as e:
        return {
            "status": "error",
            "message": f"Gemini tool not available: {e}"
        }
    
    results = tool.execute_batch(queries, top_k=top_k)
    
    return {
        "status": "success",
        "provider": "Google Gemini Grounding (1000 free/day)",
        "results": {
            query: [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "source": r.source,
                    "confidence": f"{r.relevance_score * 100:.1f}%"
                }
                for r in result_list
            ]
            for query, result_list in results.items()
        }
    }


if __name__ == "__main__":
    # 测试代码
    import os
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        test_query = "白银价格走势 2024"
        result = search_gemini(test_query, api_key=api_key)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("GEMINI_API_KEY environment variable not set")
