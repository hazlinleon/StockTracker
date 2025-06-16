import asyncio
import schedule
import time
from datetime import datetime
import logging

from crawler import NewsCrawler, init_news_sources
from analyzer import NewsAnalyzer, init_stock_data
from notifier import notifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self):
        self.is_running = False
        
    async def start(self):
        """启动调度器"""
        self.is_running = True
        logger.info("任务调度器启动")
        
        # 初始化数据
        await self.initialize_data()
        
        # 设置定时任务
        self.setup_schedules()
        
        # 运行调度循环
        while self.is_running:
            schedule.run_pending()
            await asyncio.sleep(1)
    
    def stop(self):
        """停止调度器"""
        self.is_running = False
        logger.info("任务调度器停止")
    
    async def initialize_data(self):
        """初始化基础数据"""
        try:
            logger.info("初始化基础数据...")
            await init_news_sources()
            await init_stock_data()
            logger.info("基础数据初始化完成")
        except Exception as e:
            logger.error(f"初始化数据时出错: {e}")
    
    def setup_schedules(self):
        """设置定时任务"""
        # 新闻爬取 - 每5分钟
        schedule.every(5).minutes.do(self.run_async_task, self.crawl_news_task)
        
        # 新闻分析 - 每10分钟
        schedule.every(10).minutes.do(self.run_async_task, self.analyze_news_task)
        
        # 重要警报 - 每15分钟
        schedule.every(15).minutes.do(self.run_async_task, self.send_alerts_task)
        
        # 每日总结 - 每天18:00
        schedule.every().day.at("18:00").do(self.run_async_task, self.daily_summary_task)
        
        # 清理旧数据 - 每天凌晨2:00
        schedule.every().day.at("02:00").do(self.run_async_task, self.cleanup_task)
        
        logger.info("定时任务设置完成")
    
    def run_async_task(self, coro):
        """运行异步任务"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(coro())
            loop.close()
        except Exception as e:
            logger.error(f"执行异步任务时出错: {e}")
    
    async def crawl_news_task(self):
        """新闻爬取任务"""
        try:
            logger.info("开始执行新闻爬取任务")
            async with NewsCrawler() as crawler:
                count = await crawler.crawl_all_sources()
                logger.info(f"新闻爬取完成，获取 {count} 条新闻")
        except Exception as e:
            logger.error(f"新闻爬取任务出错: {e}")
    
    async def analyze_news_task(self):
        """新闻分析任务"""
        try:
            logger.info("开始执行新闻分析任务")
            analyzer = NewsAnalyzer()
            results = await analyzer.analyze_all_unprocessed()
            logger.info(f"新闻分析完成，生成 {len(results)} 个分析结果")
        except Exception as e:
            logger.error(f"新闻分析任务出错: {e}")
    
    async def send_alerts_task(self):
        """发送警报任务"""
        try:
            logger.info("开始执行警报发送任务")
            await notifier.send_important_alerts()
            logger.info("警报发送完成")
        except Exception as e:
            logger.error(f"警报发送任务出错: {e}")
    
    async def daily_summary_task(self):
        """每日总结任务"""
        try:
            logger.info("开始执行每日总结任务")
            await notifier.send_daily_summary()
            logger.info("每日总结发送完成")
        except Exception as e:
            logger.error(f"每日总结任务出错: {e}")
    
    async def cleanup_task(self):
        """清理任务"""
        try:
            logger.info("开始执行数据清理任务")
            # 清理30天前的新闻和分析结果
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=30)
            
            # 这里可以添加具体的清理逻辑
            logger.info("数据清理完成")
        except Exception as e:
            logger.error(f"数据清理任务出错: {e}")

# 全局调度器实例
scheduler = TaskScheduler()

if __name__ == "__main__":
    asyncio.run(scheduler.start()) 