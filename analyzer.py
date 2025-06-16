import json
import asyncio
from datetime import datetime
from typing import List, Optional, Dict
import logging
import openai
from openai import AsyncOpenAI

from config import settings
from models import NewsItem, AnalysisResult, StockInfo
from database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsAnalyzer:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        
        # A股板块和概念映射
        self.sector_concepts = {
            "新能源": ["锂电池", "储能", "光伏", "风电", "新能源汽车", "充电桩"],
            "半导体": ["芯片", "集成电路", "晶圆", "封测", "设备材料"],
            "医药": ["创新药", "医疗器械", "疫苗", "CXO", "医疗服务"],
            "军工": ["航空航天", "军工电子", "船舶", "兵器"],
            "消费": ["白酒", "食品饮料", "家电", "纺织服装", "零售"],
            "科技": ["人工智能", "云计算", "大数据", "5G", "物联网"],
            "金融": ["银行", "保险", "券商", "信托"],
            "地产": ["房地产开发", "物业管理", "建筑材料"],
            "基建": ["建筑", "水泥", "钢铁", "工程机械"],
            "化工": ["石油化工", "精细化工", "农药化肥"],
        }
    
    async def analyze_all_unprocessed(self):
        """分析所有未处理的新闻"""
        news_items = await db.get_unprocessed_news(limit=50)
        logger.info(f"开始分析 {len(news_items)} 条新闻")
        
        results = []
        for item in news_items:
            try:
                result = await self.analyze_news(item)
                if result:
                    results.append(result)
                await db.mark_news_processed(str(item.id))
                await asyncio.sleep(1)  # 避免API调用过快
            except Exception as e:
                logger.error(f"分析新闻 {item.title} 时出错: {e}")
        
        logger.info(f"完成分析，生成 {len(results)} 个分析结果")
        return results
    
    async def analyze_news(self, news_item: NewsItem) -> Optional[AnalysisResult]:
        """分析单条新闻"""
        try:
            # 检查是否已经分析过
            existing = await db.get_analysis_by_news_id(str(news_item.id))
            if existing:
                return existing
            
            # 构建分析提示
            prompt = settings.ANALYSIS_PROMPT_TEMPLATE.format(
                content=f"标题: {news_item.title}\n\n内容: {news_item.content[:2000]}"
            )
            
            # 调用OpenAI API
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的A股市场分析师，擅长分析财经新闻对股市的影响。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # 解析响应
            content = response.choices[0].message.content
            analysis_data = self.parse_analysis_response(content)
            
            if not analysis_data:
                logger.warning(f"无法解析分析结果: {content}")
                return None
            
            # 补充股票信息
            analysis_data = await self.enrich_stock_info(analysis_data)
            
            # 创建分析结果
            result = AnalysisResult(
                news_id=news_item.id,
                **analysis_data
            )
            
            # 保存到数据库
            result_id = await db.create_analysis_result(result)
            logger.info(f"成功分析新闻: {news_item.title}, 重要性: {result.importance}星")
            
            return result
            
        except Exception as e:
            logger.error(f"分析新闻时出错: {e}")
            return None
    
    def parse_analysis_response(self, content: str) -> Optional[Dict]:
        """解析AI分析响应"""
        try:
            # 尝试提取JSON部分
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                data = json.loads(json_str)
                
                # 验证必需字段
                required_fields = [
                    'sentiment_score', 'sentiment_desc', 'affected_sectors',
                    'affected_concepts', 'related_stocks', 'time_range',
                    'importance', 'summary'
                ]
                
                for field in required_fields:
                    if field not in data:
                        logger.warning(f"分析结果缺少字段: {field}")
                        return None
                
                # 数据清洗和验证
                data['sentiment_score'] = max(1, min(10, int(data['sentiment_score'])))
                data['importance'] = max(1, min(5, int(data['importance'])))
                data['affected_sectors'] = [s.strip() for s in data['affected_sectors'] if s.strip()]
                data['affected_concepts'] = [c.strip() for c in data['affected_concepts'] if c.strip()]
                data['related_stocks'] = [s.strip() for s in data['related_stocks'] if s.strip() and len(s.strip()) == 6]
                
                return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
        except Exception as e:
            logger.error(f"解析分析响应时出错: {e}")
        
        return None
    
    async def enrich_stock_info(self, analysis_data: Dict) -> Dict:
        """丰富股票信息"""
        try:
            # 根据概念补充相关股票
            additional_stocks = set()
            
            for concept in analysis_data['affected_concepts']:
                concept_stocks = await db.search_stocks_by_concept(concept)
                for stock in concept_stocks[:5]:  # 限制每个概念最多5只股票
                    additional_stocks.add(stock.code)
            
            # 合并原有股票和新增股票
            all_stocks = set(analysis_data['related_stocks'])
            all_stocks.update(additional_stocks)
            analysis_data['related_stocks'] = list(all_stocks)[:20]  # 最多20只股票
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"丰富股票信息时出错: {e}")
            return analysis_data
    
    async def get_sector_sentiment(self, sector: str, days: int = 7) -> Dict:
        """获取板块情绪分析"""
        try:
            # 这里可以实现板块情绪的聚合分析
            # 暂时返回基础结构
            return {
                "sector": sector,
                "avg_sentiment": 5.5,
                "news_count": 0,
                "trend": "neutral"
            }
        except Exception as e:
            logger.error(f"获取板块情绪时出错: {e}")
            return {}
    
    async def generate_market_summary(self) -> str:
        """生成市场总结"""
        try:
            # 获取最近重要分析
            important_analysis = await db.get_important_analysis(min_importance=4)
            
            if not important_analysis:
                return "今日暂无重要市场消息。"
            
            # 构建总结提示
            news_summaries = []
            for analysis in important_analysis[:10]:  # 最多10条
                # 这里暂时简化，实际需要实现get_news_by_id方法
                news_summaries.append(f"• 重要消息 - {analysis.summary}")
            
            prompt = f"""
            请根据以下重要财经新闻，生成一份简洁的A股市场今日总结（200字以内）：
            
            {chr(10).join(news_summaries)}
            
            总结要点：
            1. 主要利好/利空消息
            2. 受影响的重点板块
            3. 整体市场情绪
            4. 投资建议（谨慎表述）
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是专业的股市分析师，要生成简洁准确的市场总结。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"生成市场总结时出错: {e}")
            return "生成市场总结时出现错误。"

# 股票概念数据初始化
STOCK_CONCEPTS = {
    "300750": {"name": "宁德时代", "sector": "新能源", "concepts": ["锂电池", "储能", "新能源汽车"]},
    "002466": {"name": "天齐锂业", "sector": "新能源", "concepts": ["锂电池", "锂矿"]},
    "600519": {"name": "贵州茅台", "sector": "消费", "concepts": ["白酒", "消费升级"]},
    "000858": {"name": "五粮液", "sector": "消费", "concepts": ["白酒", "消费升级"]},
    "000001": {"name": "平安银行", "sector": "金融", "concepts": ["银行", "金融科技"]},
    "600036": {"name": "招商银行", "sector": "金融", "concepts": ["银行", "零售银行"]},
    "600900": {"name": "长江电力", "sector": "公用事业", "concepts": ["水电", "清洁能源"]},
    "601318": {"name": "中国平安", "sector": "金融", "concepts": ["保险", "金融科技"]},
    "000002": {"name": "万科A", "sector": "地产", "concepts": ["房地产开发", "物业管理"]},
}

async def init_stock_data():
    """初始化股票数据"""
    for code, info in STOCK_CONCEPTS.items():
        stock = StockInfo(
            code=code,
            name=info["name"],
            sector=info["sector"],
            concepts=info["concepts"],
            market="SH" if code.startswith("6") else "SZ"
        )
        await db.create_stock_info(stock)
        logger.info(f"初始化股票: {info['name']} ({code})") 