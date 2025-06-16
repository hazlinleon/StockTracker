#!/usr/bin/env python3
"""
StockTracker - A股市场监控系统
主入口文件
"""

import asyncio
import argparse
import sys
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scheduler import scheduler
from api import app

def main():
    parser = argparse.ArgumentParser(description="StockTracker - A股市场监控系统")
    parser.add_argument(
        "mode",
        choices=["web", "scheduler", "all"],
        help="运行模式: web(Web服务), scheduler(后台调度器), all(同时运行)"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Web服务监听地址")
    parser.add_argument("--port", type=int, default=8000, help="Web服务端口")
    parser.add_argument("--reload", action="store_true", help="开发模式，自动重载")
    
    args = parser.parse_args()
    
    if args.mode == "web":
        print("🚀 启动StockTracker Web服务...")
        print(f"📍 访问地址: http://{args.host}:{args.port}")
        print("📚 API文档: http://{args.host}:{args.port}/docs")
        
        uvicorn.run(
            "api:app",
            host=args.host,
            port=args.port,
            reload=args.reload
        )
        
    elif args.mode == "scheduler":
        print("⏰ 启动StockTracker 调度器...")
        print("🔄 定时任务:")
        print("  • 新闻爬取: 每5分钟")
        print("  • 新闻分析: 每10分钟")  
        print("  • 重要警报: 每15分钟")
        print("  • 每日总结: 每天18:00")
        print("  • 数据清理: 每天02:00")
        
        try:
            asyncio.run(scheduler.start())
        except KeyboardInterrupt:
            print("\n🛑 调度器已停止")
            
    elif args.mode == "all":
        print("🚀 启动StockTracker 完整系统...")
        
        # 这里可以实现同时运行Web和调度器
        # 由于示例简化，暂时提示用户分别启动
        print("请分别在两个终端中运行:")
        print(f"  终端1: python main.py scheduler")
        print(f"  终端2: python main.py web --port {args.port}")

if __name__ == "__main__":
    main() 