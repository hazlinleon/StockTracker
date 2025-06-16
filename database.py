import motor.motor_asyncio
from typing import List, Optional
from datetime import datetime, timedelta
from config import settings
from models import NewsSource, NewsItem, AnalysisResult, StockInfo, Subscriber, Alert

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.DATABASE_NAME]
        
    async def close(self):
        self.client.close()
    
    # News Sources
    async def create_news_source(self, source: NewsSource) -> str:
        result = await self.db.news_sources.insert_one(source.dict(by_alias=True, exclude={"id"}))
        return str(result.inserted_id)
    
    async def get_active_news_sources(self) -> List[NewsSource]:
        cursor = self.db.news_sources.find({"is_active": True})
        sources = []
        async for doc in cursor:
            sources.append(NewsSource(**doc))
        return sources
    
    async def update_news_source_crawl_time(self, source_id: str):
        await self.db.news_sources.update_one(
            {"_id": source_id},
            {"$set": {"last_crawled": datetime.now()}}
        )
    
    # News Items
    async def create_news_item(self, item: NewsItem) -> str:
        # 检查是否已存在相同URL的新闻
        existing = await self.db.news_items.find_one({"url": item.url})
        if existing:
            return str(existing["_id"])
        
        result = await self.db.news_items.insert_one(item.dict(by_alias=True, exclude={"id"}))
        return str(result.inserted_id)
    
    async def get_unprocessed_news(self, limit: int = 10) -> List[NewsItem]:
        cursor = self.db.news_items.find({"is_processed": False}).limit(limit)
        items = []
        async for doc in cursor:
            items.append(NewsItem(**doc))
        return items
    
    async def mark_news_processed(self, news_id: str):
        await self.db.news_items.update_one(
            {"_id": news_id},
            {"$set": {"is_processed": True}}
        )
    
    async def get_recent_news(self, hours: int = 24, limit: int = 50) -> List[NewsItem]:
        from_time = datetime.now() - timedelta(hours=hours)
        cursor = self.db.news_items.find(
            {"publish_time": {"$gte": from_time}}
        ).sort("publish_time", -1).limit(limit)
        
        items = []
        async for doc in cursor:
            items.append(NewsItem(**doc))
        return items
    
    # Analysis Results
    async def create_analysis_result(self, result: AnalysisResult) -> str:
        doc = await self.db.analysis_results.insert_one(result.dict(by_alias=True, exclude={"id"}))
        return str(doc.inserted_id)
    
    async def get_analysis_by_news_id(self, news_id: str) -> Optional[AnalysisResult]:
        doc = await self.db.analysis_results.find_one({"news_id": news_id})
        if doc:
            return AnalysisResult(**doc)
        return None
    
    async def get_important_analysis(self, min_importance: int = 4) -> List[AnalysisResult]:
        cursor = self.db.analysis_results.find(
            {"importance": {"$gte": min_importance}}
        ).sort("analysis_time", -1)
        
        results = []
        async for doc in cursor:
            results.append(AnalysisResult(**doc))
        return results
    
    # Stock Info
    async def create_stock_info(self, stock: StockInfo) -> str:
        result = await self.db.stocks.insert_one(stock.dict(by_alias=True, exclude={"id"}))
        return str(result.inserted_id)
    
    async def get_stock_by_code(self, code: str) -> Optional[StockInfo]:
        doc = await self.db.stocks.find_one({"code": code})
        if doc:
            return StockInfo(**doc)
        return None
    
    async def search_stocks_by_concept(self, concept: str) -> List[StockInfo]:
        cursor = self.db.stocks.find({"concepts": {"$in": [concept]}})
        stocks = []
        async for doc in cursor:
            stocks.append(StockInfo(**doc))
        return stocks
    
    # Subscribers
    async def create_subscriber(self, subscriber: Subscriber) -> str:
        result = await self.db.subscribers.insert_one(subscriber.dict(by_alias=True, exclude={"id"}))
        return str(result.inserted_id)
    
    async def get_active_subscribers(self) -> List[Subscriber]:
        cursor = self.db.subscribers.find({"is_active": True})
        subscribers = []
        async for doc in cursor:
            subscribers.append(Subscriber(**doc))
        return subscribers
    
    async def get_subscriber_by_chat_id(self, chat_id: str) -> Optional[Subscriber]:
        doc = await self.db.subscribers.find_one({"chat_id": chat_id})
        if doc:
            return Subscriber(**doc)
        return None
    
    # Alerts
    async def create_alert(self, alert: Alert) -> str:
        result = await self.db.alerts.insert_one(alert.dict(by_alias=True, exclude={"id"}))
        return str(result.inserted_id)
    
    async def mark_alert_sent(self, alert_id: str, recipient: str):
        await self.db.alerts.update_one(
            {"_id": alert_id},
            {"$addToSet": {"sent_to": recipient}}
        )

# 全局数据库实例
db = Database() 