#!/usr/bin/env python3
"""
搜索方案路由器 - 统一接口支持多个免费搜索方案
优先级：DuckDuckGo (完全免费) > Gemini Grounding (1000/day) > 原有 SerpAPI
"""
import json
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchRouter:
    """搜索方案路由器"""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key
        self.providers = {
            "duckduckgo": self._search_duckduckgo,
            "gemini": self._search_gemini,
        }
        self.default_provider = "duckduckgo"  # 默认使用完全免费方案
    
    def search(self, query: str, provider: Optional[str] = None, top_k: int = 10, **kwargs) -> Dict:
        """统一搜索接口
        
        Args:
            query: 搜索关键词
            provider: 搜索提供商（duckduckgo/gemini/auto）
            top_k: 返回结果数量
            
        Returns:
            Dict: 搜索结果
        """
        if provider is None or provider == "auto":
            provider = self.default_provider
        
        if provider not in self.providers:
            return {
                "status": "error",
                "message": f"Unknown provider: {provider}",
                "available": list(self.providers.keys())
            }
        
        try:
            return self.providers[provider](query, top_k=top_k, **kwargs)
        except Exception as e:
            logger.error(f"Search error with {provider}: {e}")
            # 降级到 DuckDuckGo
            if provider != "duckduckgo":
                logger.info(f"Falling back to DuckDuckGo")
                return self._search_duckduckgo(query, top_k=top_k, **kwargs)
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _search_duckduckgo(self, query: str, top_k: int = 10, **kwargs) -> Dict:
        """DuckDuckGo 搜索"""
        try:
            from duckduckgo_free_search import search_free
            return search_free(query, top_k=top_k, **kwargs)
        except ImportError:
            return {
                "status": "error",
                "message": "DuckDuckGo search not available",
                "solution": "pip install duckduckgo-search"
            }
    
    def _search_gemini(self, query: str, top_k: int = 10, **kwargs) -> Dict:
        """Gemini Grounding 搜索"""
        api_key = kwargs.get("api_key") or self.gemini_api_key
        
        if not api_key:
            return {
                "status": "error",
                "message": "Gemini API Key not provided",
                "solution": "Set GEMINI_API_KEY or pass api_key parameter"
            }
        
        try:
            from gemini_grounding_search import search_gemini
            return search_gemini(query, api_key=api_key, top_k=top_k, **kwargs)
        except ImportError:
            return {
                "status": "error",
                "message": "Gemini search not available",
                "solution": "pip install google-generativeai"
            }
    
    def batch_search(self, queries: List[str], provider: Optional[str] = None, 
                    top_k: int = 10, **kwargs) -> Dict:
        """批量搜索
        
        Args:
            queries: 搜索关键词列表
            provider: 搜索提供商
            top_k: 每个查询返回结果数量
            
        Returns:
            Dict: 批量搜索结果
        """
        if provider is None or provider == "auto":
            provider = self.default_provider
        
        results = {}
        for query in queries:
            results[query] = self.search(query, provider=provider, top_k=top_k, **kwargs)
        
        return {
            "status": "success",
            "provider": provider,
            "total_queries": len(queries),
            "results": results
        }


def search(query: str, provider: str = "auto", top_k: int = 10, 
          gemini_api_key: Optional[str] = None, **kwargs) -> Dict:
    """主搜索函数 - 支持自动降级"""
    router = SearchRouter(gemini_api_key=gemini_api_key)
    return router.search(query, provider=provider, top_k=top_k, **kwargs)


def batch_search(queries: List[str], provider: str = "auto", top_k: int = 10,
                gemini_api_key: Optional[str] = None, **kwargs) -> Dict:
    """批量搜索函数"""
    router = SearchRouter(gemini_api_key=gemini_api_key)
    return router.batch_search(queries, provider=provider, top_k=top_k, **kwargs)


if __name__ == "__main__":
    # 测试代码
    import os
    
    print("=== DuckDuckGo 搜索测试 ===")
    result = search("白银价格走势 2024", provider="duckduckgo")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("\n=== Gemini 搜索测试 ===")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        result = search("白银价格走势 2024", provider="gemini", gemini_api_key=gemini_key)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("GEMINI_API_KEY not set, skipping Gemini test")
    
    print("\n=== 自动降级测试 ===")
    result = search("白银价格走势 2024", provider="auto")
    print(json.dumps(result, ensure_ascii=False, indent=2))
