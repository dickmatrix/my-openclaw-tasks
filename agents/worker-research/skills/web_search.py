#!/usr/bin/env python3
"""
WebSearch 技能接口 - 全网实时信息检索（异步版本）
支持并发搜索、速率限制处理、流式结果返回
"""
import asyncio
import httpx
import json
from typing import Dict, List, Optional, AsyncGenerator
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
    source: str
    relevance_score: float


class AsyncWebSearchTool:
    """异步全网搜索工具"""
    
    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        self.name = "web_search"
        self.description = "执行全网实时信息检索，支持竞品分析、行业趋势监控"
        self.max_results = 10
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = "https://api.serpapi.com/search"  # 示例：SerpAPI
    
    async def execute(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """异步执行搜索查询
        
        Args:
            query: 搜索关键词
            top_k: 返回结果数量
            
        Returns:
            List[SearchResult]: 搜索结果列表
        """
        if not self.validate_query(query):
            return []
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "q": query,
                    "num": min(top_k, 100),
                    "api_key": self.api_key
                }
                
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                results = []
                
                # 解析搜索结果
                for item in data.get("organic_results", [])[:top_k]:
                    results.append(SearchResult(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        source=item.get("source", ""),
                        relevance_score=0.95  # 可根据排名调整
                    ))
                
                return results
        
        except httpx.HTTPError as e:
            logger.error(f"Search API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            return []
    
    async def execute_streaming(self, query: str, top_k: int = 10) -> AsyncGenerator[SearchResult, None]:
        """流式返回搜索结果
        
        Args:
            query: 搜索关键词
            top_k: 返回结果数量
            
        Yields:
            SearchResult: 逐个搜索结果
        """
        results = await self.execute(query, top_k)
        for result in results:
            yield result
            await asyncio.sleep(0.1)  # 模拟流式处理
    
    async def execute_batch(self, queries: List[str], top_k: int = 10) -> Dict[str, List[SearchResult]]:
        """并发执行多个搜索查询
        
        Args:
            queries: 搜索关键词列表
            top_k: 每个查询返回结果数量
            
        Returns:
            Dict[str, List[SearchResult]]: 查询结果映射
        """
        tasks = [self.execute(query, top_k) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = {}
        for query, result in zip(queries, results):
            if isinstance(result, Exception):
                logger.error(f"Error searching for '{query}': {result}")
                output[query] = []
            else:
                output[query] = result
        
        return output
    
    def validate_query(self, query: str) -> bool:
        """验证搜索查询有效性"""
        if not query or len(query.strip()) < 2:
            return False
        if len(query) > 500:
            return False
        return True


async def search_async(query: str, api_key: Optional[str] = None, 
                      top_k: int = 10, **kwargs) -> Dict:
    """异步搜索主函数"""
    tool = AsyncWebSearchTool(api_key=api_key)
    
    if not tool.validate_query(query):
        return {"status": "error", "message": "Invalid query"}
    
    results = await tool.execute(query, top_k=top_k)
    
    return {
        "status": "success",
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


async def search_batch_async(queries: List[str], api_key: Optional[str] = None,
                            top_k: int = 10, **kwargs) -> Dict:
    """异步批量搜索"""
    tool = AsyncWebSearchTool(api_key=api_key)
    results = await tool.execute_batch(queries, top_k=top_k)
    
    return {
        "status": "success",
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


def main(query: str, **kwargs) -> Dict:
    """同步包装器 - 保持向后兼容"""
    return asyncio.run(search_async(query, **kwargs))


if __name__ == "__main__":
    # 测试代码
    test_query = "白银价格走势 2024"
    result = asyncio.run(search_async(test_query))
    print(json.dumps(result, ensure_ascii=False, indent=2))
