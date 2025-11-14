"""
网页爬虫数据源
"""
from typing import List, Dict, Any, Set
from urllib.parse import urljoin, urlparse
import asyncio
import httpx
from bs4 import BeautifulSoup
from loguru import logger

from app.services.datasource.base import BaseDataSource


class WebCrawlerDataSource(BaseDataSource):
    """网页爬虫数据源"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.visited_urls: Set[str] = set()
        self.max_depth = config.get("max_depth", 3)
        self.delay = config.get("delay", 1)  # 秒
        self.user_agent = config.get("user_agent", "CoreMind Bot 1.0")
    
    async def connect(self) -> bool:
        """测试起始URL"""
        try:
            start_url = self.config.get("start_url")
            if not start_url:
                raise ValueError("未指定起始URL")
            
            # 测试连接
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    start_url,
                    headers={"User-Agent": self.user_agent},
                    timeout=10.0,
                    follow_redirects=True
                )
                response.raise_for_status()
            
            self.connected = True
            logger.info(f"成功连接到网页: {start_url}")
            return True
            
        except Exception as e:
            logger.error(f"连接网页失败: {str(e)}")
            return False
    
    async def fetch_data(self) -> List[Dict[str, Any]]:
        """爬取网页数据"""
        if not self.connected:
            await self.connect()
        
        results = []
        start_url = self.config.get("start_url")
        
        try:
            # 开始爬取
            await self._crawl_recursive(start_url, 0, results)
            
            logger.info(f"爬取了 {len(results)} 个网页")
            return results
            
        except Exception as e:
            logger.error(f"爬取网页失败: {str(e)}")
            return []
    
    async def _crawl_recursive(
        self,
        url: str,
        depth: int,
        results: List[Dict[str, Any]]
    ):
        """递归爬取"""
        # 检查深度限制
        if depth > self.max_depth:
            return
        
        # 检查是否已访问
        if url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        
        try:
            # 延迟
            if self.delay > 0 and len(self.visited_urls) > 1:
                await asyncio.sleep(self.delay)
            
            # 获取网页内容
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": self.user_agent},
                    timeout=30.0,
                    follow_redirects=True
                )
                response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 提取标题
            title = soup.title.string if soup.title else url
            
            # 提取正文内容
            content = self._extract_content(soup)
            
            if content:
                results.append({
                    "title": title,
                    "content": self.preprocess_content(content),
                    "metadata": {
                        "url": url,
                        "depth": depth,
                    }
                })
            
            # 提取链接并继续爬取
            if depth < self.max_depth:
                links = self._extract_links(soup, url)
                for link in links:
                    await self._crawl_recursive(link, depth + 1, results)
            
        except Exception as e:
            logger.warning(f"爬取URL失败 {url}: {str(e)}")
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取网页正文内容"""
        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()
        
        # 尝试找到主要内容区域
        main_content = (
            soup.find("main") or
            soup.find("article") or
            soup.find("div", class_="content") or
            soup.find("div", id="content") or
            soup.body
        )
        
        if main_content:
            # 提取文本
            text = main_content.get_text(separator=" ", strip=True)
            return text
        
        return ""
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """提取页面中的链接"""
        links = []
        base_domain = urlparse(base_url).netloc
        
        # 获取链接过滤配置
        include_patterns = self.config.get("include_patterns", [])
        exclude_patterns = self.config.get("exclude_patterns", [])
        same_domain_only = self.config.get("same_domain_only", True)
        
        for link in soup.find_all("a", href=True):
            href = link["href"]
            
            # 构建完整URL
            full_url = urljoin(base_url, href)
            
            # 解析URL
            parsed = urlparse(full_url)
            
            # 只处理http/https链接
            if parsed.scheme not in ["http", "https"]:
                continue
            
            # 同域名限制
            if same_domain_only and parsed.netloc != base_domain:
                continue
            
            # URL过滤
            if include_patterns:
                if not any(pattern in full_url for pattern in include_patterns):
                    continue
            
            if exclude_patterns:
                if any(pattern in full_url for pattern in exclude_patterns):
                    continue
            
            links.append(full_url)
        
        return links
    
    async def disconnect(self) -> bool:
        """断开连接"""
        self.visited_urls.clear()
        self.connected = False
        return True

