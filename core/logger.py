import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from core.config import settings

def setup_logging():
    """
    配置全局日志
    - 控制台输出
    - 文件输出 (按大小轮转)
    - 统一格式
    """
    log_level = settings.logging_level
    log_format = settings.logging_format
    log_datefmt = settings.logging_datefmt
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    # 使用 get_logging_level_value 获取 int 类型的日志级别
    root_logger.setLevel(settings.get_logging_level_value())
    
    # 清除现有的 handlers
    root_logger.handlers = []
    
    # 创建 formatter
    formatter = logging.Formatter(fmt=log_format, datefmt=log_datefmt)
    
    # 1. 控制台 Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 2. 文件 Handler (如果配置了日志文件路径)
    # 假设我们在 config 中可以获取日志目录，这里默认 logs/app.log
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, "app.log")
    
    # 10MB per file, max 5 backups
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 调整第三方库的日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)

# 导出 logger 供其他模块使用 (其实直接用 logging.getLogger(__name__) 也可以，但这里可以做一些封装)
def get_logger(name: str):
    return logging.getLogger(name)
