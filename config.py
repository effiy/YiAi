"""应用配置管理"""
import os
from typing import List, Optional


class Config:
    """应用配置类（单例模式）"""
    
    _instance: Optional['Config'] = None
    _initialized: bool = False
    
    # 默认配置常量
    DEFAULT_CORS_ORIGINS = "https://effiy.cn,https://m.effiy.cn,http://localhost:3000,http://localhost:8000"
    DEFAULT_RSS_SCHEDULER_ENABLED = "true"
    DEFAULT_AUTH_MIDDLEWARE_ENABLED = "true"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置（只执行一次）"""
        if not self._initialized:
            self._cors_origins: Optional[List[str]] = None
            self._initialized = True
    
    def get_cors_origins(self) -> List[str]:
        """获取CORS允许的来源列表（缓存结果）"""
        if self._cors_origins is None:
            cors_origins_env = os.getenv("CORS_ORIGINS", self.DEFAULT_CORS_ORIGINS)
            self._cors_origins = [
                o.strip() for o in cors_origins_env.split(",") if o.strip()
            ]
        return self._cors_origins
    
    def allow_any_origin(self) -> bool:
        """是否允许任意来源"""
        origins = self.get_cors_origins()
        return len(origins) == 1 and origins[0] == "*"
    
    def is_rss_scheduler_enabled(self) -> bool:
        """是否启用RSS定时任务"""
        return os.getenv("ENABLE_RSS_SCHEDULER", self.DEFAULT_RSS_SCHEDULER_ENABLED).lower() == "true"
    
    def is_auth_middleware_enabled(self) -> bool:
        """是否启用认证中间件"""
        return os.getenv("ENABLE_AUTH_MIDDLEWARE", self.DEFAULT_AUTH_MIDDLEWARE_ENABLED).lower() == "true"


# 创建全局配置实例（保持向后兼容）
_config_instance = Config()

