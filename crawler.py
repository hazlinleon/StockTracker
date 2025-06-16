import asyncio
import aiohttp
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin, urlparse
import logging
import re

from config import settings
from models import NewsItem, NewsSource
from database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsCrawler:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT),
            headers={"User-Agent": settings.USER_AGENT}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def crawl_all_sources(self):
        """爬取所有活跃的新闻源"""
        sources = await db.get_active_news_sources()
        logger.info(f"开始爬取 {len(sources)} 个新闻源")
        
        tasks = []
        for source in sources:
            tasks.append(self.crawl_source(source))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_news = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"爬取源 {sources[i].name} 时出错: {result}")
            else:
                total_news += result
        
        logger.info(f"本次爬取完成，共获取 {total_news} 条新闻")
        return total_news
    
    async def crawl_source(self, source: NewsSource) -> int:
        """爬取单个新闻源"""
        try:
            if source.source_type == "sina_finance":
                return await self.crawl_sina_finance()
            elif source.source_type == "cnstock":
                return await self.crawl_cnstock()
            elif source.source_type == "csrc":
                return await self.crawl_csrc()
            elif source.source_type == "sse":
                return await self.crawl_sse()
            elif source.source_type == "szse":
                return await self.crawl_szse()
            elif source.source_type == "stats":
                return await self.crawl_stats()
            else:
                return await self.crawl_generic_rss(source)
        except Exception as e:
            logger.error(f"爬取 {source.name} 时出错: {e}")
            return 0
        finally:
            await db.update_news_source_crawl_time(str(source.id))
    
    async def crawl_sina_finance(self) -> int:
        """爬取新浪财经"""
        url = "https://feed.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=50&page=1"
        
        async with self.session.get(url) as response:
            data = await response.json()
            
        news_count = 0
        if data.get("result") and data["result"].get("data"):
            for item in data["result"]["data"]:
                try:
                    news_item = NewsItem(
                        title=item.get("title", ""),
                        content=await self.get_page_content(item.get("url", "")),
                        url=item.get("url", ""),
                        source_name="新浪财经",
                        source_type="news",
                        publish_time=datetime.fromtimestamp(int(item.get("ctime", 0)))
                    )
                    await db.create_news_item(news_item)
                    news_count += 1
                except Exception as e:
                    logger.error(f"处理新浪财经新闻时出错: {e}")
        
        return news_count
    
    async def crawl_cnstock(self) -> int:
        """爬取中国证券网"""
        url = "http://www.cnstock.com/v_news/sns_yw/index.html"
        
        async with self.session.get(url) as response:
            text = await response.text()
        
        soup = BeautifulSoup(text, 'html.parser')
        news_items = soup.find_all('div', class_='news_item')
        
        news_count = 0
        for item in news_items:
            try:
                title_elem = item.find('a')
                if title_elem:
                    title = title_elem.get_text().strip()
                    url = urljoin("http://www.cnstock.com", title_elem.get('href'))
                    
                    time_elem = item.find('span', class_='time')
                    pub_time = datetime.now()
                    if time_elem:
                        time_str = time_elem.get_text().strip()
                        pub_time = self.parse_time(time_str)
                    
                    content = await self.get_page_content(url)
                    
                    news_item = NewsItem(
                        title=title,
                        content=content,
                        url=url,
                        source_name="中国证券网",
                        source_type="news",
                        publish_time=pub_time
                    )
                    await db.create_news_item(news_item)
                    news_count += 1
            except Exception as e:
                logger.error(f"处理中国证券网新闻时出错: {e}")
        
        return news_count
    
    async def crawl_csrc(self) -> int:
        """爬取证监会公告"""
        url = "http://www.csrc.gov.cn/newsite/zjhxwfb/"
        
        async with self.session.get(url) as response:
            text = await response.text()
        
        soup = BeautifulSoup(text, 'html.parser')
        news_items = soup.find_all('li', class_='news_item')
        
        news_count = 0
        for item in news_items:
            try:
                link_elem = item.find('a')
                if link_elem:
                    title = link_elem.get_text().strip()
                    url = urljoin("http://www.csrc.gov.cn", link_elem.get('href'))
                    
                    time_elem = item.find('span', class_='date')
                    pub_time = datetime.now()
                    if time_elem:
                        time_str = time_elem.get_text().strip()
                        pub_time = self.parse_time(time_str)
                    
                    content = await self.get_page_content(url)
                    
                    news_item = NewsItem(
                        title=title,
                        content=content,
                        url=url,
                        source_name="中国证监会",
                        source_type="official",
                        publish_time=pub_time
                    )
                    await db.create_news_item(news_item)
                    news_count += 1
            except Exception as e:
                logger.error(f"处理证监会公告时出错: {e}")
        
        return news_count
    
    async def crawl_sse(self) -> int:
        """爬取上交所公告"""
        url = "http://www.sse.com.cn/news/newslist/"
        
        async with self.session.get(url) as response:
            text = await response.text()
        
        soup = BeautifulSoup(text, 'html.parser')
        news_items = soup.find_all('div', class_='news-item')
        
        news_count = 0
        for item in news_items:
            try:
                link_elem = item.find('a')
                if link_elem:
                    title = link_elem.get_text().strip()
                    url = urljoin("http://www.sse.com.cn", link_elem.get('href'))
                    
                    time_elem = item.find('span', class_='time')
                    pub_time = datetime.now()
                    if time_elem:
                        time_str = time_elem.get_text().strip()
                        pub_time = self.parse_time(time_str)
                    
                    content = await self.get_page_content(url)
                    
                    news_item = NewsItem(
                        title=title,
                        content=content,
                        url=url,
                        source_name="上海证券交易所",
                        source_type="official",
                        publish_time=pub_time
                    )
                    await db.create_news_item(news_item)
                    news_count += 1
            except Exception as e:
                logger.error(f"处理上交所公告时出错: {e}")
        
        return news_count
    
    async def crawl_szse(self) -> int:
        """爬取深交所公告"""
        url = "http://www.szse.cn/news/index.html"
        
        async with self.session.get(url) as response:
            text = await response.text()
        
        soup = BeautifulSoup(text, 'html.parser')
        news_items = soup.find_all('tr')
        
        news_count = 0
        for item in news_items:
            try:
                link_elem = item.find('a')
                if link_elem:
                    title = link_elem.get_text().strip()
                    url = urljoin("http://www.szse.cn", link_elem.get('href'))
                    
                    tds = item.find_all('td')
                    pub_time = datetime.now()
                    if len(tds) > 1:
                        time_str = tds[-1].get_text().strip()
                        pub_time = self.parse_time(time_str)
                    
                    content = await self.get_page_content(url)
                    
                    news_item = NewsItem(
                        title=title,
                        content=content,
                        url=url,
                        source_name="深圳证券交易所",
                        source_type="official",
                        publish_time=pub_time
                    )
                    await db.create_news_item(news_item)
                    news_count += 1
            except Exception as e:
                logger.error(f"处理深交所公告时出错: {e}")
        
        return news_count
    
    async def crawl_stats(self) -> int:
        """爬取统计局公告"""
        url = "http://www.stats.gov.cn/tjsj/"
        
        async with self.session.get(url) as response:
            text = await response.text()
        
        soup = BeautifulSoup(text, 'html.parser')
        news_items = soup.find_all('li')
        
        news_count = 0
        for item in news_items:
            try:
                link_elem = item.find('a')
                if link_elem and 'href' in link_elem.attrs:
                    title = link_elem.get_text().strip()
                    url = urljoin("http://www.stats.gov.cn", link_elem.get('href'))
                    
                    time_elem = item.find('span')
                    pub_time = datetime.now()
                    if time_elem:
                        time_str = time_elem.get_text().strip()
                        pub_time = self.parse_time(time_str)
                    
                    content = await self.get_page_content(url)
                    
                    news_item = NewsItem(
                        title=title,
                        content=content,
                        url=url,
                        source_name="国家统计局",
                        source_type="official",
                        publish_time=pub_time
                    )
                    await db.create_news_item(news_item)
                    news_count += 1
            except Exception as e:
                logger.error(f"处理统计局公告时出错: {e}")
        
        return news_count
    
    async def crawl_generic_rss(self, source: NewsSource) -> int:
        """爬取通用RSS源"""
        try:
            feed = feedparser.parse(source.url)
            news_count = 0
            
            for entry in feed.entries:
                try:
                    content = entry.get('description', '')
                    if hasattr(entry, 'content'):
                        content = entry.content[0].value
                    
                    pub_time = datetime.now()
                    if hasattr(entry, 'published_parsed'):
                        pub_time = datetime(*entry.published_parsed[:6])
                    
                    news_item = NewsItem(
                        title=entry.title,
                        content=content,
                        url=entry.link,
                        source_name=source.name,
                        source_type=source.source_type,
                        publish_time=pub_time
                    )
                    await db.create_news_item(news_item)
                    news_count += 1
                except Exception as e:
                    logger.error(f"处理RSS条目时出错: {e}")
            
            return news_count
        except Exception as e:
            logger.error(f"爬取RSS源 {source.url} 时出错: {e}")
            return 0
    
    async def get_page_content(self, url: str) -> str:
        """获取网页正文内容"""
        try:
            async with self.session.get(url) as response:
                text = await response.text()
            
            soup = BeautifulSoup(text, 'html.parser')
            
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 尝试找到正文内容
            content_selectors = [
                'div.content', 'div.article-content', 'div.news-content',
                'div.main-content', 'article', '.article-body', '.content-body'
            ]
            
            content = ""
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text()
                    break
            
            if not content:
                # 如果没找到特定选择器，获取所有p标签内容
                paragraphs = soup.find_all('p')
                content = '\n'.join([p.get_text() for p in paragraphs])
            
            # 清理文本
            content = re.sub(r'\s+', ' ', content).strip()
            return content[:5000]  # 限制长度
            
        except Exception as e:
            logger.error(f"获取页面内容失败 {url}: {e}")
            return ""
    
    def parse_time(self, time_str: str) -> datetime:
        """解析时间字符串"""
        try:
            # 处理各种时间格式
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
                "%m-%d %H:%M",
                "%Y年%m月%d日",
                "%m月%d日"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue
            
            # 如果都解析失败，返回当前时间
            return datetime.now()
        except:
            return datetime.now()

# 初始化数据源
async def init_news_sources():
    """初始化新闻源"""
    sources = [
        NewsSource(name="新浪财经", url="https://finance.sina.com.cn/", source_type="sina_finance"),
        NewsSource(name="中国证券网", url="http://www.cnstock.com/", source_type="cnstock"),
        NewsSource(name="中国证监会", url="http://www.csrc.gov.cn/", source_type="csrc"),
        NewsSource(name="上海证券交易所", url="http://www.sse.com.cn/", source_type="sse"),
        NewsSource(name="深圳证券交易所", url="http://www.szse.cn/", source_type="szse"),
        NewsSource(name="国家统计局", url="http://www.stats.gov.cn/", source_type="stats"),
    ]
    
    for source in sources:
        await db.create_news_source(source)
        logger.info(f"初始化新闻源: {source.name}") 