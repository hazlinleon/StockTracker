# StockTracker - A股市场智能监控系统

🚀 基于AI的财经新闻分析与股票监控平台

## 📋 项目简介

StockTracker是一个智能的A股市场监控系统，通过实时爬取财经新闻和官方公告，使用大语言模型进行智能分析，自动识别利好利空消息、影响板块和相关个股，并通过多种渠道推送重要信息给订阅用户。

## 🔥 核心功能

### 📰 多源数据监控
- **财经媒体**: 新浪财经、中国证券网、金融界等主流财经网站
- **官方公告**: 证监会、上交所、深交所官方发布
- **统计数据**: 国家统计局重要经济数据发布
- **支持扩展**: 可轻松添加RSS源和自定义爬虫

### 🤖 AI智能分析
- **情绪分析**: 1-10分量化利好利空程度
- **影响识别**: 自动识别受影响的行业板块和概念
- **个股匹配**: 智能匹配相关核心个股代码
- **重要性评级**: 1-5星重要性评级系统
- **市场总结**: 每日自动生成市场热点总结

### 📱 多渠道推送
- **Telegram Bot**: 实时推送重要消息
- **企业微信**: 支持企业微信群消息推送
- **Web界面**: 提供完整的Web管理和查看界面
- **API接口**: RESTful API支持第三方集成

### 🎯 智能订阅
- **个性化订阅**: 支持按重要性、板块、个股定制
- **推送策略**: 灵活的消息过滤和推送频率控制
- **多账号管理**: 支持多用户独立订阅设置

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   数据采集层    │    │   AI分析层      │    │   通知推送层    │
│                 │    │                 │    │                 │
│ • 新闻爬虫      │───▶│ • OpenAI GPT    │───▶│ • Telegram      │
│ • 公告监控      │    │ • 情绪分析      │    │ • 企业微信      │
│ • RSS订阅       │    │ • 板块识别      │    │ • Web推送       │
│ • 定时任务      │    │ • 个股匹配      │    │ • 邮件通知      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
           │                       │                       │
           ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                        数据存储层                                │
│ • MongoDB (新闻、分析结果、用户数据)                            │
│ • Redis (缓存、任务队列)                                        │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- MongoDB 4.4+
- Redis 6.0+

### 1. 克隆项目
```bash
git clone https://github.com/yourusername/StockTracker.git
cd StockTracker
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
# 复制环境变量模板
cp env_example.txt .env

# 编辑配置文件
vim .env
```

配置说明：
```bash
# 必需配置
MONGODB_URL=mongodb://localhost:27017
OPENAI_API_KEY=your_openai_api_key_here

# 可选配置
TELEGRAM_BOT_TOKEN=your_telegram_bot_token  # Telegram推送
WECHAT_WEBHOOK_URL=your_wechat_webhook      # 企业微信推送
```

### 4. 启动服务

#### 启动Web管理界面
```bash
python main.py web
```
访问 http://localhost:8000 查看系统状态和管理界面

#### 启动后台调度器
```bash
python main.py scheduler
```

#### 查看API文档
访问 http://localhost:8000/docs 查看完整的API文档

## 📚 使用指南

### Web界面功能

1. **系统状态**: 查看爬虫运行状态、数据统计
2. **新闻浏览**: 浏览最新抓取的财经新闻
3. **分析结果**: 查看AI分析的重要消息
4. **订阅管理**: 管理用户订阅设置
5. **手动操作**: 手动触发爬虫、分析任务

### API接口使用

#### 获取最新新闻
```bash
curl "http://localhost:8000/news?limit=10&hours=24"
```

#### 获取重要分析
```bash
curl "http://localhost:8000/analysis?min_importance=4"
```

#### 订阅消息推送
```bash
curl -X POST "http://localhost:8000/subscribe" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "telegram",
    "chat_id": "your_chat_id",
    "subscribe_types": ["important_only"],
    "interested_sectors": ["新能源", "半导体"]
  }'
```

#### 获取市场总结
```bash
curl "http://localhost:8000/summary"
```

### Telegram Bot设置

1. 创建Telegram Bot (联系 @BotFather)
2. 获取Bot Token并配置到环境变量
3. 获取您的Chat ID
4. 通过API订阅推送服务

### 定时任务说明

系统自动执行以下定时任务：
- **新闻爬取**: 每5分钟执行一次
- **AI分析**: 每10分钟分析未处理的新闻
- **重要警报**: 每15分钟检查并推送重要消息
- **每日总结**: 每天18:00生成市场总结
- **数据清理**: 每天02:00清理30天前的旧数据

## 🔧 配置详解

### 新闻源配置

系统默认监控以下源，可通过数据库配置添加更多：

```python
# 主流财经媒体
"新浪财经": "https://finance.sina.com.cn/"
"中国证券网": "http://www.cnstock.com/"

# 官方机构
"中国证监会": "http://www.csrc.gov.cn/"
"上海证券交易所": "http://www.sse.com.cn/"
"深圳证券交易所": "http://www.szse.cn/"
"国家统计局": "http://www.stats.gov.cn/"
```

### AI分析配置

可在 `config.py` 中自定义分析提示词：

```python
ANALYSIS_PROMPT_TEMPLATE = """
请分析以下财经新闻，并按照JSON格式返回分析结果：
新闻内容：{content}

返回JSON格式包含：
- sentiment_score: 利好利空评分(1-10)
- affected_sectors: 影响板块
- related_stocks: 相关个股代码
- importance: 重要性(1-5星)
- summary: 简要分析
"""
```

### 订阅类型说明

- `all`: 接收所有消息
- `important_only`: 仅接收4星以上重要消息
- `sectors`: 按关注板块过滤
- `daily_summary`: 接收每日市场总结

## 🛠️ 开发指南

### 项目结构
```
StockTracker/
├── main.py              # 主入口文件
├── config.py            # 配置文件
├── models.py            # 数据模型
├── database.py          # 数据库操作
├── crawler.py           # 新闻爬虫
├── analyzer.py          # AI分析模块
├── notifier.py          # 消息推送
├── scheduler.py         # 任务调度
├── api.py               # Web API
└── requirements.txt     # 依赖包
```

### 添加新的新闻源

1. 在 `crawler.py` 中添加爬虫方法
2. 在数据库中添加新闻源配置
3. 重启调度器生效

### 扩展通知渠道

1. 在 `notifier.py` 中添加新的推送方法
2. 更新订阅模型支持新平台
3. 在API中添加相应配置选项

## 📊 监控指标

系统提供以下监控指标：
- 每日新闻抓取数量
- AI分析成功率
- 重要消息推送数量
- 用户订阅活跃度
- 系统运行状态

## ⚠️ 注意事项

1. **数据合规**: 请确保遵守各网站的robots.txt规则
2. **API限制**: OpenAI API有调用频率限制，注意控制请求频率
3. **数据存储**: 建议定期备份MongoDB数据
4. **性能优化**: 大量数据时建议优化数据库查询和索引

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📄 开源协议

本项目采用 MIT 协议 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📮 联系方式

- 项目Issues: [GitHub Issues](https://github.com/yourusername/StockTracker/issues)
- 邮箱: your.email@example.com

---

⭐ 如果这个项目对您有帮助，请给个Star支持一下！
