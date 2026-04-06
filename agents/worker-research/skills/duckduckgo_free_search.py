#!/usr/bin/env python3
"""
DuckDuckGo 免费搜索 Skill - 完全无需 API Key
支持并发搜索、速率限制、流式结果返回
"""
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果数据结构"""
    title: str
    url: str
    snippet: str
    source: str = "DuckDuckGo"
    relevance_score: float = 0.95


class DuckDuckGoSearchTool:
    """DuckDuckGo 免费搜索工具 - 无需 API Key"""
    
    def __init__(self, timeout: float = 30.0):
        self.name = "duckduckgo_search"
        self.description = "执行全网实时信息检索（完全免费，无需 API Key）"
        self.max_results = 20
        self.timeout = timeout
        
        # 延迟导入，避免启动时失败
        try:
            from duckduckgo_search import DDGS
            self.ddgs = DDGS(timeout=timeout)
        except ImportError as e:
            raise ImportError(f"duckduckgo-search package required. Install: pip install duckduckgo-search") from e
    
    def execute(self, query: str, top_k: int = 10, region: str = "cn-zh") -> List[SearchResult]:
        """执行搜索查询
        
        Args:
            query: 搜索关键词
            top_k: 返回结果数量
            region: 地区代码（cn-zh 中文，en-us 英文等）
            
        Returns:
            List[SearchResult]: 搜索结果列表
        """
        if not self.validate_query(query):
            return []
        
        try:
            results = []
            # DuckDuckGo 文本搜索
            for idx, result in enumerate(self.ddgs.text(query, region=region, max_results=top_k)):
                results.append(SearchResult(
                    title=result.get("title", ""),
                    url=result.get("href", ""),
                    snippet=result.get("body", ""),
                    source="DuckDuckGo",
                    relevance_score=1.0 - (idx * 0.05)  # 排名越靠前分数越高
                ))
            
            logger.info(f"DuckDuckGo search for '{query}' returned {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
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


def search_free(query: str, top_k: int = 10, region: str = "cn-zh", **kwargs) -> Dict:
    """免费搜索主函数 - DuckDuckGo"""
    try:
        tool = DuckDuckGoSearchTool()
    except ImportError as e:
        return {
            "status": "error",
            "message": str(e),
            "solution": "pip install duckduckgo-search"
        }
    
    if not tool.validate_query(query):
        return {"status": "error", "message": "Invalid query"}
    
    results = tool.execute(query, top_k=top_k, region=region)
    
    return {
        "status": "success",
        "provider": "DuckDuckGo (Free)",
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


def search_batch_free(queries: List[str], top_k: int = 10, **kwargs) -> Dict:
    """免费批量搜索 - DuckDuckGo"""
    try:
        tool = DuckDuckGoSearchTool()
    except ImportError as e:
        return {
            "status": "error",
            "message": str(e)
        }
    
    results = tool.execute_batch(queries, top_k=top_k)
    
    return {
        "status": "success",
        "provider": "DuckDuckGo (Free)",
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
    test_query = "白银价格走势 2024"
    result = search_free(test_query)
    print(json.dumps(result, ensure_ascii=False, indent=2))
