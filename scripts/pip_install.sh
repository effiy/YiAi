# 安装爬虫库，用于网页抓取功能
pip install -U crawl4ai

# 安装playwright及其依赖，为爬虫提供浏览器环境
python -m playwright install --with-deps chromium

# 安装FastAPI和uvicorn，用于创建和运行Web服务器
pip install -U fastapi uvicorn