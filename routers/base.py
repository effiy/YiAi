from fastapi import APIRouter, HTTPException
import logging
import time
from database import db
# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["base"])

@router.get("/health")
async def health_check():
    """
    检查系统健康状态
    返回详细的连接状态信息，包括数据库连接状态
    """
    try:
        # 确保数据库已初始化
        if not hasattr(db, '_initialized') or not db._initialized:
            await db.initialize()

        # 测试 MySQL 连接
        mysql_status = "healthy"
        try:
            async with db.mysql.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
        except Exception as e:
            mysql_status = f"unhealthy: {str(e)}"
            logger.error(f"MySQL health check failed: {str(e)}")

        # 测试 MongoDB 连接
        mongo_status = "healthy"
        try:
            await db.mongodb.db.command("ping")
        except Exception as e:
            mongo_status = f"unhealthy: {str(e)}"
            logger.error(f"MongoDB health check failed: {str(e)}")

        return {
            "status": "ok",
            "timestamp": time.time(),
            "version": "1.0",
            "services": {
                "mysql": mysql_status,
                "mongodb": mongo_status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )