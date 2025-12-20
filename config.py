"""应用配置管理"""
import os
from typing import List


class Config:
    """应用配置类"""
    
    # CORS配置
    @staticmethod
    def get_cors_origins() -> List[str]:
        """获取CORS允许的来源列表"""
        cors_origins_env = os.getenv(
            "CORS_ORIGINS", 
            "https://effiy.cn,https://m.effiy.cn,http://localhost:3000,http://localhost:8000"
        )
        origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
        return origins
    
    @staticmethod
    def allow_any_origin() -> bool:
        """是否允许任意来源"""
        origins = Config.get_cors_origins()
        return len(origins) == 1 and origins[0] == "*"
    
    # RSS配置
    @staticmethod
    def is_rss_scheduler_enabled() -> bool:
        """是否启用RSS定时任务"""
        return os.getenv("ENABLE_RSS_SCHEDULER", "true").lower() == "true"
    
    # 中间件配置
    @staticmethod
    def is_auth_middleware_enabled() -> bool:
        """是否启用认证中间件"""
        return os.getenv("ENABLE_AUTH_MIDDLEWARE", "true").lower() == "true"

