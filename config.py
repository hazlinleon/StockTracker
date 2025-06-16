import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库配置
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = "stock_tracker"
    
    # Redis配置
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # OpenAI配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    # 通知配置
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    WECHAT_WEBHOOK_URL: str = os.getenv("WECHAT_WEBHOOK_URL", "")
    
    # 爬虫配置
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    REQUEST_TIMEOUT: int = 30
    RETRY_TIMES: int = 3
    
    # 监控源配置
    NEWS_SOURCES: List[str] = [
        "https://finance.sina.com.cn/",
        "https://www.cnstock.com/",
        "https://www.cs.com.cn/",
        "https://www.jrj.com.cn/"
    ]
    
    # 官方公告源
    OFFICIAL_SOURCES: List[str] = [
        "http://www.csrc.gov.cn/",  # 证监会
        "http://www.sse.com.cn/",   # 上交所
        "http://www.szse.cn/",      # 深交所
        "http://www.stats.gov.cn/"  # 统计局
    ]
    
    # 分析配置
    ANALYSIS_PROMPT_TEMPLATE: str = """
    请分析以下财经新闻，并按照JSON格式返回分析结果：
    
    新闻内容：{content}
    
    请从以下方面进行分析：
    1. 利好/利空程度（1-10分，1为极度利空，10为极度利好）
    2. 影响的板块和概念（如新能源、半导体、医药等）
    3. 可能影响的核心个股代码（A股6位数字代码）
    4. 影响时间范围（短期/中期/长期）
    5. 重要性评级（1-5星）
    
    返回JSON格式：
    {{
        "sentiment_score": 6,
        "sentiment_desc": "偏利好",
        "affected_sectors": ["新能源", "电池"],
        "affected_concepts": ["锂电池", "储能"],
        "related_stocks": ["300750", "002466"],
        "time_range": "中期",
        "importance": 4,
        "summary": "简要总结"
    }}
    """
    
    class Config:
        env_file = ".env"

settings = Settings() 