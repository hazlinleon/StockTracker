@echo off
echo 🚀 StockTracker 安装脚本 (Windows)
echo ==========================

:: 检查Python版本
echo 📋 检查Python版本...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.8+
    echo    下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version
echo ✅ Python已安装

:: 检查MongoDB
echo 📋 检查MongoDB...
where mongod >nul 2>&1
if errorlevel 1 (
    echo ⚠️  警告: 未检测到MongoDB，请确保MongoDB已安装并运行
    echo    下载地址: https://www.mongodb.com/try/download/community
) else (
    echo ✅ MongoDB已安装
)

:: 创建虚拟环境
echo 🔧 创建Python虚拟环境...
if not exist "venv" (
    python -m venv venv
    echo ✅ 虚拟环境创建成功
) else (
    echo ✅ 虚拟环境已存在
)

:: 激活虚拟环境并安装依赖
echo 📦 安装Python依赖包...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ 依赖包安装失败，请检查网络连接和requirements.txt
    pause
    exit /b 1
) else (
    echo ✅ 依赖包安装成功
)

:: 创建环境配置文件
echo ⚙️  配置环境变量...
if not exist ".env" (
    copy env_example.txt .env
    echo ✅ 已创建.env配置文件，请编辑其中的配置项
    echo 📝 必需配置项：
    echo    - MONGODB_URL: MongoDB连接URL
    echo    - OPENAI_API_KEY: OpenAI API密钥
    echo 📝 可选配置项：
    echo    - TELEGRAM_BOT_TOKEN: Telegram机器人令牌
    echo    - WECHAT_WEBHOOK_URL: 企业微信Webhook
) else (
    echo ✅ .env配置文件已存在
)

:: 创建启动脚本
echo 🚀 创建启动脚本...
echo @echo off > start_web.bat
echo call venv\Scripts\activate.bat >> start_web.bat
echo python main.py web >> start_web.bat
echo pause >> start_web.bat

echo @echo off > start_scheduler.bat
echo call venv\Scripts\activate.bat >> start_scheduler.bat
echo python main.py scheduler >> start_scheduler.bat
echo pause >> start_scheduler.bat

echo.
echo 🎉 安装完成！
echo ==========================
echo 📝 下一步操作：
echo 1. 编辑 .env 文件，配置必要的API密钥
echo 2. 确保MongoDB服务正在运行
echo 3. 启动Web服务: start_web.bat
echo 4. 启动调度器: start_scheduler.bat
echo.
echo 🌐 Web界面: http://localhost:8000
echo 📚 API文档: http://localhost:8000/docs
echo.
echo 如有问题，请查看README.md获取详细说明
pause 