from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import List, Optional
from datetime import datetime, timedelta

from config import settings
from models import NewsItem, AnalysisResult, Subscriber
from database import db
from crawler import NewsCrawler
from analyzer import NewsAnalyzer
from notifier import notifier

app = FastAPI(title="StockTracker", description="A股市场监控系统")

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    print("StockTracker 启动中...")
    
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    await db.close()

# 主页
@app.get("/", response_class=HTMLResponse)
async def home():
    """系统主页"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>StockTracker - A股市场监控系统</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            .header { text-align: center; margin-bottom: 40px; }
            .feature { margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 5px; }
            .api-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .api-item { padding: 15px; background: #e3f2fd; border-radius: 5px; }
            .status { padding: 10px; background: #d4edda; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 StockTracker</h1>
                <h2>A股市场智能监控系统</h2>
                <p>基于AI的财经新闻分析与股票监控平台</p>
            </div>
            
            <div class="feature">
                <h3>🔥 核心功能</h3>
                <ul>
                    <li>📰 实时监控主流财经媒体、证监会、交易所、统计局等官方公告</li>
                    <li>🤖 AI智能分析新闻利好利空程度，识别影响板块和概念</li>
                    <li>📈 自动匹配相关核心个股，提供投资参考</li>
                    <li>📱 多渠道推送重要消息：Telegram、企业微信等</li>
                    <li>📊 生成每日市场总结和板块情绪分析</li>
                </ul>
            </div>
            
            <div class="status">
                <h3>📊 系统状态</h3>
                <p>✅ 系统运行正常 | 🕐 当前时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
            </div>
            
            <h3>🔧 API接口</h3>
            <div class="api-list">
                <div class="api-item">
                    <h4>GET /news</h4>
                    <p>获取最新新闻列表</p>
                </div>
                <div class="api-item">
                    <h4>GET /analysis</h4>
                    <p>获取分析结果</p>
                </div>
                <div class="api-item">
                    <h4>POST /subscribe</h4>
                    <p>订阅消息推送</p>
                </div>
                <div class="api-item">
                    <h4>GET /summary</h4>
                    <p>获取市场总结</p>
                </div>
                <div class="api-item">
                    <h4>POST /crawl</h4>
                    <p>手动触发爬虫</p>
                </div>
                <div class="api-item">
                    <h4>GET /docs</h4>
                    <p>查看完整API文档</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

# 新闻相关API
@app.get("/news", response_model=List[NewsItem])
async def get_news(limit: int = 20, hours: int = 24):
    """获取最新新闻"""
    try:
        news = await db.get_recent_news(hours=hours, limit=limit)
        return news
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis", response_model=List[AnalysisResult])
async def get_analysis(min_importance: int = 1, limit: int = 20):
    """获取分析结果"""
    try:
        if min_importance > 1:
            results = await db.get_important_analysis(min_importance=min_importance)
        else:
            # 获取所有分析结果的逻辑需要在database.py中实现
            results = await db.get_important_analysis(min_importance=1)
        return results[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/summary")
async def get_market_summary():
    """获取市场总结"""
    try:
        analyzer = NewsAnalyzer()
        summary = await analyzer.generate_market_summary()
        return {"summary": summary, "generated_at": datetime.now()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 订阅管理API
@app.post("/subscribe")
async def subscribe(
    platform: str,
    chat_id: str,
    subscribe_types: List[str] = ["all"],
    interested_sectors: List[str] = [],
    interested_stocks: List[str] = []
):
    """订阅消息推送"""
    try:
        # 检查是否已存在
        existing = await db.get_subscriber_by_chat_id(chat_id)
        if existing:
            return {"message": "已经订阅过了", "subscriber_id": str(existing.id)}
        
        subscriber = Subscriber(
            user_id=chat_id,
            platform=platform,
            chat_id=chat_id,
            subscribe_types=subscribe_types,
            interested_sectors=interested_sectors,
            interested_stocks=interested_stocks
        )
        
        subscriber_id = await db.create_subscriber(subscriber)
        return {"message": "订阅成功", "subscriber_id": subscriber_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/subscribers")
async def get_subscribers():
    """获取订阅者列表"""
    try:
        subscribers = await db.get_active_subscribers()
        return {"count": len(subscribers), "subscribers": subscribers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 手动触发任务API
@app.post("/crawl")
async def manual_crawl(background_tasks: BackgroundTasks):
    """手动触发爬虫"""
    async def crawl_task():
        async with NewsCrawler() as crawler:
            await crawler.crawl_all_sources()
    
    background_tasks.add_task(crawl_task)
    return {"message": "爬虫任务已启动"}

@app.post("/analyze")
async def manual_analyze(background_tasks: BackgroundTasks):
    """手动触发分析"""
    async def analyze_task():
        analyzer = NewsAnalyzer()
        await analyzer.analyze_all_unprocessed()
    
    background_tasks.add_task(analyze_task)
    return {"message": "分析任务已启动"}

@app.post("/notify")
async def manual_notify(background_tasks: BackgroundTasks):
    """手动触发通知"""
    async def notify_task():
        await notifier.send_important_alerts()
    
    background_tasks.add_task(notify_task)
    return {"message": "通知任务已启动"}

# 统计信息API
@app.get("/stats")
async def get_stats():
    """获取系统统计信息"""
    try:
        # 这里需要在database.py中实现统计查询方法
        stats = {
            "total_news": 0,  # await db.count_news()
            "total_analysis": 0,  # await db.count_analysis()
            "active_subscribers": len(await db.get_active_subscribers()),
            "system_status": "running",
            "last_update": datetime.now()
        }
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 