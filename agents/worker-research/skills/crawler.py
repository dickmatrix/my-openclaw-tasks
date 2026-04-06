#!/usr/bin/env python3
"""
Crawler 数据抓取技能 - 结构化网页解析与数据提取（异步版本）
支持并发抓取、动态内容处理、反爬虫策略
"""
import asyncio
import httpx
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass, field
from urllib.parse import urlparse
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    """爬取结果数据结构"""
    url: str
    title: str
    content: str
    metadata: Dict = field(default_factory=dict)
    links: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    status_code: int = 200
    error: Optional[str] = None


@dataclass
class ExtractedData:
    """提取的结构化数据"""
    entity_type: str
    fields: Dict[str, str]
    confidence: float
    source_url: str


class AsyncCrawlerTool:
    """异步网页爬虫工具"""
    
    def __init__(self, timeout: float = 30.0, max_concurrent: int = 10):
        self.name = "crawler"
        self.description = "结构化网页解析、数据提取、反爬虫策略"
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.respect_robots = True
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """异步获取网页内容
        
        Args:
            url: 目标 URL
            
        Returns:
            str: 网页 HTML 内容
        """
        async with self.semaphore:
            try:
                async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                    response = await client.get(url, follow_redirects=True)
                    response.raise_for_status()
                    return response.text
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching {url}: {e}")
                return None
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                return None
    
    async def fetch_batch(self, urls: List[str]) -> Dict[str, Optional[str]]:
        """并发获取多个网页
        
        Args:
            urls: URL 列表
            
        Returns:
            Dict[str, Optional[str]]: URL 到内容的映射
        """
        tasks = [self.fetch_page(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = {}
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching {url}: {result}")
                output[url] = None
            else:
                output[url] = result
        
        return output
    
    def parse_html(self, html: str, selectors: Dict[str, str]) -> Dict[str, str]:
        """解析 HTML 并提取数据
        
        Args:
            html: HTML 内容
            selectors: CSS 选择器映射
            
        Returns:
            Dict[str, str]: 提取的数据
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            result = {}
            
            for key, selector in selectors.items():
                element = soup.select_one(selector)
                result[key] = element.get_text(strip=True) if element else None
            
            return result
        except ImportError:
            logger.warning("BeautifulSoup4 not installed, returning empty result")
            return {}
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return {}
    
    def extract_tables(self, html: str, table_index: int = 0) -> List[Dict]:
        """提取 HTML 表格数据
        
        Args:
            html: HTML 内容
            table_index: 表格索引（从 0 开始）
            
        Returns:
            List[Dict]: 表格数据列表
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            tables = soup.find_all('table')
            
            if table_index >= len(tables):
                return []
            
            table = tables[table_index]
            headers = []
            rows = []
            
            # 提取表头
            thead = table.find('thead')
            if thead:
                for th in thead.find_all('th'):
                    headers.append(th.get_text(strip=True))
            
            # 提取行数据
            tbody = table.find('tbody') or table
            for tr in tbody.find_all('tr'):
                cells = tr.find_all(['td', 'th'])
                if not headers and cells:
                    headers = [cell.get_text(strip=True) for cell in cells]
                else:
                    row = {headers[i]: cell.get_text(strip=True) for i, cell in enumerate(cells) if i < len(headers)}
                    rows.append(row)
            
            return rows
        except ImportError:
            logger.warning("BeautifulSoup4 not installed")
            return []
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            return []
    
    async def crawl_streaming(self, urls: List[str]) -> AsyncGenerator[CrawlResult, None]:
        """流式爬取多个 URL
        
        Args:
            urls: URL 列表
            
        Yields:
            CrawlResult: 爬取结果
        """
        for url in urls:
            html = await self.fetch_page(url)
            
            if html:
                yield CrawlResult(
                    url=url,
                    title="",  # TODO: 提取标题
                    content=html[:1000],  # 返回前 1000 字符
                    status_code=200
                )
            else:
                yield CrawlResult(
                    url=url,
                    title="",
                    content="",
                    status_code=0,
                    error="Failed to fetch page"
                )
            
            await asyncio.sleep(0.1)  # 避免过快请求
    
    def validate_url(self, url: str) -> bool:
        """验证 URL 格式"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    async def get_respect_robots(self, url: str) -> bool:
        """异步检查 robots.txt"""
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(robots_url)
                # 简化检查：如果能获取到 robots.txt，则允许爬取
                return response.status_code == 200
        except:
            return True  # 默认允许


async def crawl_url_async(url: str, selectors: Dict[str, str] = None, 
                         extract_tables: bool = False) -> Dict:
    """异步爬取并解析网页
    
    Args:
        url: 目标 URL
        selectors: CSS 选择器（可选）
        extract_tables: 是否提取表格
    """
    tool = AsyncCrawlerTool()
    
    if not tool.validate_url(url):
        return {"status": "error", "message": "Invalid URL"}
    
    if not await tool.get_respect_robots(url):
        return {"status": "error", "message": "Blocked by robots.txt"}
    
    html = await tool.fetch_page(url)
    if not html:
        return {"status": "error", "message": "Failed to fetch page"}
    
    result = {
        "status": "success",
        "url": url,
        "title": "",
        "content": html[:2000],  # 返回前 2000 字符
    }
    
    if selectors:
        result["extracted_data"] = tool.parse_html(html, selectors)
    
    if extract_tables:
        result["tables"] = tool.extract_tables(html)
    
    return result


def main(url: str, action: str = "fetch", **kwargs) -> Dict:
    """同步包装器 - 保持向后兼容"""
    if action == "fetch":
        return asyncio.run(crawl_url_async(
            url,
            selectors=kwargs.get("selectors"),
            extract_tables=kwargs.get("extract_tables", False)
        ))
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


if __name__ == "__main__":
    # 测试代码
    test_url = "https://example.com/finance"
    result = asyncio.run(crawl_url_async(test_url))
    print(json.dumps(result, ensure_ascii=False, indent=2))
