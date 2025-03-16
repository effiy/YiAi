from fastapi import APIRouter, HTTPException
import logging
import time

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["base"])

@router.get("/")
async def test_db_connections():
    """
    测试数据库连接的健康状态
    返回详细的连接状态信息，包括延迟和错误信息
    """
    try:
        return {
            "timestamp": time.time(),
            "version": "1.0"
        }
    except Exception as e:
        logger.error(f"Error during health check: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )