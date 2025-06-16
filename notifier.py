import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict
import logging
from telegram import Bot
from telegram.error import TelegramError

from config import settings
from models import AnalysisResult, NewsItem, Subscriber, Alert
from database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.telegram_bot = None
        if settings.TELEGRAM_BOT_TOKEN:
            self.telegram_bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    
    async def send_important_alerts(self):
        """发送重要警报"""
        try:
            # 获取重要分析结果
            important_analysis = await db.get_important_analysis(min_importance=4)
            
            for analysis in important_analysis:
                # 这里暂时简化，实际需要实现get_news_by_id方法
                news_item = NewsItem(
                    title="重要消息",
                    content="",
                    url="",
                    source_name="系统",
                    source_type="system",
                    publish_time=datetime.now()
                )
                await self.create_and_send_alert(news_item, analysis)
                    
        except Exception as e:
            logger.error(f"发送重要警报时出错: {e}")
    
    async def create_and_send_alert(self, news_item: NewsItem, analysis: AnalysisResult):
        """创建并发送警报"""
        try:
            # 创建警报消息
            alert_content = self.format_alert_message(news_item, analysis)
            
            alert = Alert(
                news_id=news_item.id,
                analysis_id=analysis.id,
                title=news_item.title,
                content=alert_content,
                importance=analysis.importance
            )
            
            alert_id = await db.create_alert(alert)
            
            # 获取订阅者并发送
            subscribers = await db.get_active_subscribers()
            
            for subscriber in subscribers:
                if self.should_send_to_subscriber(subscriber, analysis):
                    await self.send_to_subscriber(subscriber, alert_content)
                    await db.mark_alert_sent(alert_id, subscriber.chat_id)
                    
        except Exception as e:
            logger.error(f"创建并发送警报时出错: {e}")
    
    def format_alert_message(self, news_item: NewsItem, analysis: AnalysisResult) -> str:
        """格式化警报消息"""
        
        # 情绪图标
        sentiment_icon = "📈" if analysis.sentiment_score >= 7 else "📉" if analysis.sentiment_score <= 4 else "📊"
        
        # 重要性星级
        importance_stars = "⭐" * analysis.importance
        
        message = f"""
🚨 {importance_stars} 市场重要消息 {importance_stars}

{sentiment_icon} **{news_item.title}**

📊 **影响分析**:
• 利好/利空评分: {analysis.sentiment_score}/10 ({analysis.sentiment_desc})
• 影响时间: {analysis.time_range}
• 重要程度: {analysis.importance}/5星

🏭 **影响板块**: {', '.join(analysis.affected_sectors)}
🏷️ **相关概念**: {', '.join(analysis.affected_concepts)}

📈 **关注个股**: 
{self.format_stock_list(analysis.related_stocks)}

💡 **简要分析**: {analysis.summary}

🕐 发布时间: {news_item.publish_time.strftime('%Y-%m-%d %H:%M')}
🔗 原文链接: {news_item.url}

---
📱 StockTracker 为您提供实时市场监控
"""
        return message.strip()
    
    def format_stock_list(self, stock_codes: List[str]) -> str:
        """格式化股票列表"""
        if not stock_codes:
            return "暂无"
        
        # 限制显示数量
        displayed_stocks = stock_codes[:8]
        result = ', '.join(displayed_stocks)
        
        if len(stock_codes) > 8:
            result += f" 等{len(stock_codes)}只"
            
        return result
    
    def should_send_to_subscriber(self, subscriber: Subscriber, analysis: AnalysisResult) -> bool:
        """判断是否应该发送给订阅者"""
        # 检查订阅类型
        if "all" in subscriber.subscribe_types:
            return True
            
        if "important_only" in subscriber.subscribe_types and analysis.importance >= 4:
            return True
            
        if "sectors" in subscriber.subscribe_types:
            # 检查是否关注相关板块
            for sector in analysis.affected_sectors:
                if sector in subscriber.interested_sectors:
                    return True
                    
            # 检查是否关注相关股票
            for stock in analysis.related_stocks:
                if stock in subscriber.interested_stocks:
                    return True
        
        return False
    
    async def send_to_subscriber(self, subscriber: Subscriber, message: str):
        """发送消息给订阅者"""
        try:
            if subscriber.platform == "telegram" and self.telegram_bot:
                await self.send_telegram_message(subscriber.chat_id, message)
            elif subscriber.platform == "wechat":
                await self.send_wechat_message(subscriber.chat_id, message)
            else:
                logger.warning(f"不支持的平台: {subscriber.platform}")
                
        except Exception as e:
            logger.error(f"发送消息给 {subscriber.chat_id} 时出错: {e}")
    
    async def send_telegram_message(self, chat_id: str, message: str):
        """发送Telegram消息"""
        try:
            await self.telegram_bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            logger.info(f"成功发送Telegram消息到 {chat_id}")
            
        except TelegramError as e:
            logger.error(f"Telegram发送失败: {e}")
        except Exception as e:
            logger.error(f"发送Telegram消息时出错: {e}")
    
    async def send_wechat_message(self, webhook_url: str, message: str):
        """发送企业微信消息"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "msgtype": "text",
                    "text": {
                        "content": message
                    }
                }
                
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("成功发送企业微信消息")
                    else:
                        logger.error(f"企业微信发送失败: {response.status}")
                        
        except Exception as e:
            logger.error(f"发送企业微信消息时出错: {e}")
    
    async def send_daily_summary(self):
        """发送每日市场总结"""
        try:
            from analyzer import NewsAnalyzer
            analyzer = NewsAnalyzer()
            summary = await analyzer.generate_market_summary()
            
            summary_message = f"""
📊 **今日A股市场总结**

{summary}

---
📱 StockTracker 每日为您总结市场动态
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
            
            # 发送给所有订阅者
            subscribers = await db.get_active_subscribers()
            for subscriber in subscribers:
                if "daily_summary" in subscriber.subscribe_types or "all" in subscriber.subscribe_types:
                    await self.send_to_subscriber(subscriber, summary_message)
                    
        except Exception as e:
            logger.error(f"发送每日总结时出错: {e}")

# 全局通知管理器
notifier = NotificationManager() 