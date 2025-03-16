from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database import get_db, mongodb
import logging
import time
from typing import Dict, Any
from prometheus_client import Counter, Histogram

# 配置日志
logger = logging.getLogger(__name__)

# 定义 Prometheus 指标
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests count')
REQUEST_LATENCY = Histogram('api_request_latency_seconds', 'API request latency')
DB_ERROR_COUNT = Counter('db_error_total', 'Total database error count', ['db_type'])

router = APIRouter(prefix="/api", tags=["base"])

async def check_database_connection(db: Session) -> Dict[str, Any]:
    """检查数据库连接并返回详细状态"""
    status = {
        "mysql": {"status": "unknown", "latency": 0},
        "mongodb": {"status": "unknown", "latency": 0}
    }
    
    # MySQL 检查
    try:
        start_time = time.time()
        mysql_result = db.execute("SELECT 1").fetchone()
        mysql_latency = time.time() - start_time
        status["mysql"] = {
            "status": "healthy" if mysql_result else "error",
            "latency": round(mysql_latency * 1000, 2)  # 转换为毫秒
        }
    except SQLAlchemyError as e:
        logger.error(f"MySQL connection error: {str(e)}")
        DB_ERROR_COUNT.labels(db_type="mysql").inc()
        status["mysql"] = {
            "status": "error",
            "error": str(e)
        }

    # MongoDB 检查
    try:
        start_time = time.time()
        mongo_result = await mongodb.test_collection.find_one({"test": "data"})
        mongo_latency = time.time() - start_time
        status["mongodb"] = {
            "status": "healthy" if mongo_result is not None else "not_found",
            "latency": round(mongo_latency * 1000, 2)  # 转换为毫秒
        }
    except Exception as e:
        logger.error(f"MongoDB connection error: {str(e)}")
        DB_ERROR_COUNT.labels(db_type="mongodb").inc()
        status["mongodb"] = {
            "status": "error",
            "error": str(e)
        }

    return status

@router.get("/")
async def test_db_connections(db: Session = Depends(get_db)):
    """
    测试数据库连接的健康状态
    返回详细的连接状态信息，包括延迟和错误信息
    """
    REQUEST_COUNT.inc()
    with REQUEST_LATENCY.time():
        try:
            status = await check_database_connection(db)
            
            # 计算总体健康状态
            is_healthy = all(
                status[db_type]["status"] == "healthy" 
                for db_type in ["mysql", "mongodb"]
            )
            
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "timestamp": time.time(),
                "databases": status,
                "version": "1.0"
            }
        except Exception as e:
            logger.error(f"Error during health check: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={"error": "Internal server error", "message": str(e)}
            )