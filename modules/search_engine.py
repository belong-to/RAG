import requests
import json
import os
import logging
import streamlit as st
from typing import List, Dict, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('search_engine')

# 默认API密钥
SERPAPI_KEY = "b6f6c5e20e3cec2d33d297aaad32ea0b9a5708255fbc7ffa914528332b728306"  # 需要替换为实际的SERP API密钥
BING_API_KEY = "your_bing_api_key"  # 需要替换为实际的Bing API密钥
GOOGLE_API_KEY = "8c0fe3d38b100440f44ad188dd858c1736401309"  # 需要替换为实际的Google API密钥

class SearchResult:
    """搜索结果类"""
    def __init__(self, title: str, link: str, snippet: str, source: str):
        self.title = title
        self.link = link
        self.snippet = snippet
        self.source = source  # 搜索引擎来源
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "link": self.link,
            "snippet": self.snippet,
            "source": self.source
        }
    
    def __str__(self) -> str:
        return f"标题: {self.title}\n链接: {self.link}\n摘要: {self.snippet}\n来源: {self.source}"

class SearchEngine:
    """搜索引擎基类"""
    def __init__(self, api_key: str = None):
        self.api_key = api_key
    
    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """执行搜索
        
        Args:
            query: 搜索查询
            num_results: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        raise NotImplementedError("子类必须实现search方法")

class SerpApiSearch(SearchEngine):
    """使用SerpApi进行搜索"""
    def __init__(self, api_key: str = None):
        super().__init__(api_key or SERPAPI_KEY)
    
    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        try:
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.api_key,
                "num": num_results
            }
            
            response = requests.get("https://serpapi.com/search", params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "organic_results" in data:
                for item in data["organic_results"][:num_results]:
                    results.append(SearchResult(
                        title=item.get("title", ""),
                        link=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        source="SerpApi (Google)"
                    ))
            return results
        except Exception as e:
            logger.error(f"SerpApi搜索失败: {e}")
            return []

class BingSearch(SearchEngine):
    """使用Bing搜索API"""
    def __init__(self, api_key: str = None):
        super().__init__(api_key or BING_API_KEY)
    
    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        try:
            headers = {
                "Ocp-Apim-Subscription-Key": self.api_key
            }
            params = {
                "q": query,
                "count": num_results,
                "mkt": "zh-CN"
            }
            
            response = requests.get(
                "https://api.bing.microsoft.com/v7.0/search",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "webPages" in data and "value" in data["webPages"]:
                for item in data["webPages"]["value"][:num_results]:
                    results.append(SearchResult(
                        title=item.get("name", ""),
                        link=item.get("url", ""),
                        snippet=item.get("snippet", ""),
                        source="Bing"
                    ))
            return results
        except Exception as e:
            logger.error(f"Bing搜索失败: {e}")
            return []

class MockSearchEngine(SearchEngine):
    """模拟搜索引擎（用于测试或API不可用时）"""
    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        # 返回一些模拟的搜索结果
        results = [
            SearchResult(
                title=f"关于 {query} 的模拟结果 {i+1}",
                link=f"https://example.com/result{i+1}",
                snippet=f"这是关于 {query} 的模拟搜索结果摘要。这只是一个示例，实际使用时请配置真实的搜索API。",
                source="模拟搜索引擎"
            ) for i in range(num_results)
        ]
        return results

def get_search_engine(engine_name: str, api_keys: Dict[str, str] = None) -> SearchEngine:
    """获取搜索引擎实例
    
    Args:
        engine_name: 搜索引擎名称
        api_keys: API密钥字典
        
    Returns:
        搜索引擎实例
    """
    if api_keys is None:
        api_keys = {}
    
    if engine_name == "SerpApi":
        return SerpApiSearch(api_keys.get("serpapi", SERPAPI_KEY))
    elif engine_name == "Bing":
        return BingSearch(api_keys.get("bing", BING_API_KEY))
    elif engine_name == "Mock":
        return MockSearchEngine()
    else:
        logger.warning(f"不支持的搜索引擎: {engine_name}，使用模拟搜索引擎代替")
        return MockSearchEngine()

def format_search_results(results: List[SearchResult]) -> str:
    """将搜索结果格式化为字符串
    
    Args:
        results: 搜索结果列表
        
    Returns:
        格式化后的字符串
    """
    if not results:
        return "未找到相关搜索结果。"
    
    formatted = "搜索引擎结果:\n\n"
    for i, result in enumerate(results, 1):
        formatted += f"[{i}] {result.title}\n"
        formatted += f"链接: {result.link}\n"
        formatted += f"摘要: {result.snippet}\n"
        formatted += f"来源: {result.source}\n\n"
    
    return formatted