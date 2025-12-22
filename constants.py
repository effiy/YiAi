"""应用常量定义"""
import os

# 服务器配置
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = int(os.getenv("PORT", "8000"))

# 分页配置
DEFAULT_PAGE_SIZE = 2000
MAX_PAGE_SIZE = 8000
MIN_PAGE_SIZE = 1

# 数据库集合名称
COLLECTION_SESSIONS = "sessions"
COLLECTION_RSS = "rss"
COLLECTION_CHAT_RECORDS = "chat_records"
COLLECTION_PET_DATA_SYNC = "pet_data_sync"

# 用户ID相关
DEFAULT_USER_ID = "default_user"

# Uvicorn配置
UVICORN_RELOAD = os.getenv("UVICORN_RELOAD", "true").lower() == "true"
UVICORN_LIMIT_CONCURRENCY = 1000
UVICORN_LIMIT_MAX_REQUESTS = 10000
UVICORN_TIMEOUT_KEEP_ALIVE = 5

