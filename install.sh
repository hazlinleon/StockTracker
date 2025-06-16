#!/bin/bash

echo "🚀 StockTracker 安装脚本"
echo "=========================="

# 检查Python版本
echo "📋 检查Python版本..."
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

echo "✅ Python版本: $python_version"

# 检查MongoDB
echo "📋 检查MongoDB..."
if ! command -v mongod &> /dev/null; then
    echo "⚠️  警告: 未检测到MongoDB，请确保MongoDB已安装并运行"
    echo "   安装指南: https://docs.mongodb.com/manual/installation/"
else
    echo "✅ MongoDB已安装"
fi

# 检查Redis (可选)
echo "📋 检查Redis..."
if ! command -v redis-server &> /dev/null; then
    echo "⚠️  警告: 未检测到Redis，某些功能可能无法使用"
    echo "   安装指南: https://redis.io/download"
else
    echo "✅ Redis已安装"
fi

# 创建虚拟环境
echo "🔧 创建Python虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境并安装依赖
echo "📦 安装Python依赖包..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ 依赖包安装成功"
else
    echo "❌ 依赖包安装失败，请检查网络连接和requirements.txt"
    exit 1
fi

# 创建环境配置文件
echo "⚙️  配置环境变量..."
if [ ! -f ".env" ]; then
    cp env_example.txt .env
    echo "✅ 已创建.env配置文件，请编辑其中的配置项"
    echo "📝 必需配置项："
    echo "   - MONGODB_URL: MongoDB连接URL"
    echo "   - OPENAI_API_KEY: OpenAI API密钥"
    echo "📝 可选配置项："
    echo "   - TELEGRAM_BOT_TOKEN: Telegram机器人令牌"
    echo "   - WECHAT_WEBHOOK_URL: 企业微信Webhook"
else
    echo "✅ .env配置文件已存在"
fi

# 创建启动脚本
echo "🚀 创建启动脚本..."
cat > start_web.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python main.py web
EOF

cat > start_scheduler.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python main.py scheduler
EOF

chmod +x start_web.sh start_scheduler.sh

echo ""
echo "🎉 安装完成！"
echo "=========================="
echo "📝 下一步操作："
echo "1. 编辑 .env 文件，配置必要的API密钥"
echo "2. 确保MongoDB服务正在运行"
echo "3. 启动Web服务: ./start_web.sh"
echo "4. 启动调度器: ./start_scheduler.sh"
echo ""
echo "🌐 Web界面: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo ""
echo "如有问题，请查看README.md获取详细说明" 