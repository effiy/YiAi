"""应用配置管理"""
import os
import yaml
import logging
from typing import List, Optional, Any, Dict, Union
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

class Config:
    """应用配置类（单例模式）"""

    _instance: Optional['Config'] = None
    _initialized: bool = False
    _config_data: Dict[str, Any] = {}

    # 默认配置常量
    DEFAULT_CORS_ORIGINS = "*"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化配置（只执行一次）"""
        if not self._initialized:
            self._load_config_file()
            self._initialized = True

    def _load_config_file(self):
        """加载 config.yaml 文件"""
        config_path = os.path.join(os.getcwd(), "config.yaml")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config_data = yaml.safe_load(f) or {}
                logger.info(f"已加载配置文件: {config_path}")
            except Exception as e:
                logger.error(f"加载配置文件失败 {config_path}: {e}")
                self._config_data = {}
        else:
            logger.info(f"配置文件未找到，将使用默认值和环境变量: {config_path}")
            self._config_data = {}

    def _get_nested(self, path: str) -> Any:
        """从嵌套字典中获取值"""
        keys = path.split('.')
        value = self._config_data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    def get(self, yaml_path: str, default_env_var: str = None, default: Any = None, type_cast: type = None) -> Any:
        """
        获取配置值，优先级：
        1. 环境变量 (变量名可配置)
        2. YAML 配置文件
        3. 默认值
        
        Args:
            yaml_path: YAML 配置路径 (e.g. "server.port")
            default_env_var: 默认环境变量名
            default: 默认值
            type_cast: 类型转换函数
            
        Returns:
            Any: 配置值
            
        Example:
            >>> port = config.get("server.port", "PORT", 8000, int)
        """
        val = None
        
        # 1. 确定环境变量名称
        env_var_name = default_env_var
        
        # 尝试从 YAML 的 env_configs 获取自定义环境变量名
        # 注意：这里我们假设 env_configs 是扁平的，键就是 yaml_path
        env_configs = self._config_data.get('env_configs', {})
        if isinstance(env_configs, dict) and yaml_path in env_configs:
            env_var_name = env_configs[yaml_path]

        # 2. 尝试从环境变量获取
        if env_var_name and env_var_name in os.environ:
            val = os.environ[env_var_name]
        
        # 3. 尝试从 YAML 获取 (跳过 env_configs 节点)
        if val is None:
            yaml_val = self._get_nested(yaml_path)
            if yaml_val is not None:
                val = yaml_val
        
        # 4. 使用默认值
        if val is None:
            val = default

        # 5. 类型转换
        if type_cast and val is not None:
            try:
                if type_cast == bool:
                    if isinstance(val, bool):
                        return val
                    if isinstance(val, str):
                        return val.lower() in ('true', '1', 'yes', 'on')
                    return bool(val)
                if type_cast == list and isinstance(val, str):
                    # 简单处理逗号分隔的字符串转列表
                    return [item.strip() for item in val.split(',') if item.strip()]
                return type_cast(val)
            except Exception as e:
                logger.warning(f"配置类型转换失败 {yaml_path}/{env_var_name}: {e}, 使用原值")
                return val
            
        return val

    # --- Server Config ---
    @property
    def server_host(self) -> str:
        return self.get("server.host", "HOST", "0.0.0.0", str)

    @property
    def server_port(self) -> int:
        return self.get("server.port", "PORT", 8000, int)

    @property
    def server_reload(self) -> bool:
        return self.get("server.reload", "UVICORN_RELOAD", True, bool)

    @property
    def uvicorn_limit_concurrency(self) -> int:
        return self.get("server.uvicorn.limit_concurrency", "UVICORN_LIMIT_CONCURRENCY", 1000, int)

    @property
    def uvicorn_limit_max_requests(self) -> int:
        return self.get("server.uvicorn.limit_max_requests", "UVICORN_LIMIT_MAX_REQUESTS", 10000, int)

    @property
    def uvicorn_timeout_keep_alive(self) -> int:
        return self.get("server.uvicorn.timeout_keep_alive", "UVICORN_TIMEOUT_KEEP_ALIVE", 5, int)

    # --- Pagination Config ---
    @property
    def pagination_default_size(self) -> int:
        return self.get("pagination.default_size", "DEFAULT_PAGE_SIZE", 2000, int)

    @property
    def pagination_max_size(self) -> int:
        return self.get("pagination.max_size", "MAX_PAGE_SIZE", 8000, int)

    @property
    def pagination_min_size(self) -> int:
        return self.get("pagination.min_size", "MIN_PAGE_SIZE", 1, int)

    # --- User Config ---
    @property
    def default_user_id(self) -> str:
        return self.get("user.default_id", "DEFAULT_USER_ID", "default_user", str)

    # --- Static Config ---
    @property
    def static_base_dir(self) -> str:
        return self.get("static.base_dir", "STATIC_BASE_DIR", "./static", str)

    @property
    def static_max_zip_size(self) -> int:
        mb = self.get("static.max_zip_size_mb", "STATIC_MAX_ZIP_SIZE_MB", 100, int)
        return mb * 1024 * 1024

    # --- CORS Config ---
    def get_cors_origins(self) -> List[str]:
        """获取CORS允许的来源列表"""
        origins = self.get("server.cors_origins", "CORS_ORIGINS", ["*"], list)
        if isinstance(origins, str) and origins == "*":
            return ["*"]
        return origins

    def allow_any_origin(self) -> bool:
        """是否允许任意来源"""
        return self.get("server.cors_allow_any", "CORS_ALLOW_ANY_ORIGIN", True, bool)

    # --- Database Config ---
    @property
    def mongodb_url(self) -> str:
        return self.get("database.mongodb.url", "MONGODB_URL", "mongodb://localhost:27017", str)

    @property
    def mongodb_db_name(self) -> str:
        return self.get("database.mongodb.database", "MONGODB_DATABASE", "yi_ai", str)

    @property
    def mongodb_pool_size(self) -> int:
        return self.get("database.mongodb.pool_size", "MONGODB_POOL_SIZE", 10, int)
    
    @property
    def mongodb_max_pool_size(self) -> int:
        return self.get("database.mongodb.max_pool_size", "MONGODB_MAX_POOL_SIZE", 50, int)

    @property
    def collection_sessions(self) -> str:
        return self.get("database.mongodb.collections.sessions", "COLLECTION_SESSIONS", "sessions", str)

    @property
    def collection_rss(self) -> str:
        return self.get("database.mongodb.collections.rss", "COLLECTION_RSS", "rss", str)

    @property
    def collection_chat_records(self) -> str:
        return self.get("database.mongodb.collections.chat_records", "COLLECTION_CHAT_RECORDS", "chat_records", str)

    @property
    def collection_pet_data_sync(self) -> str:
        return self.get("database.mongodb.collections.pet_data_sync", "COLLECTION_PET_DATA_SYNC", "pet_data_sync", str)
    
    @property
    def collection_seeds(self) -> str:
        return self.get("database.mongodb.collections.seeds", "COLLECTION_SEEDS", "seeds", str)
    
    @property
    def collection_oss_file_tags(self) -> str:
        return self.get("database.mongodb.collections.oss_file_tags", "COLLECTION_OSS_FILE_TAGS", "oss_file_tags", str)
    
    @property
    def collection_oss_file_info(self) -> str:
        return self.get("database.mongodb.collections.oss_file_info", "COLLECTION_OSS_FILE_INFO", "oss_file_info", str)

    # --- OSS Config ---
    @property
    def oss_access_key(self) -> str:
        return self.get("oss.access_key", "OSS_ACCESS_KEY_ID", "", str)
    
    @property
    def oss_secret_key(self) -> str:
        return self.get("oss.secret_key", "OSS_ACCESS_KEY_SECRET", "", str)
    
    @property
    def oss_endpoint(self) -> str:
        return self.get("oss.endpoint", "OSS_ENDPOINT", "", str)
    
    @property
    def oss_bucket(self) -> str:
        return self.get("oss.bucket", "OSS_BUCKET_NAME", "", str)
    
    @property
    def oss_domain(self) -> str:
        return self.get("oss.domain", "OSS_DOMAIN", "", str)
    
    @property
    def oss_max_file_size(self) -> int:
        # 返回字节数
        mb = self.get("oss.max_file_size_mb", "OSS_MAX_FILE_SIZE", 50, int)
        return mb * 1024 * 1024
    
    @property
    def oss_allowed_extensions(self) -> List[str]:
        return self.get("oss.allowed_extensions", "OSS_ALLOWED_EXTENSIONS", [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".epub", ".md"], list)

    # --- RSS Config ---
    def is_rss_scheduler_enabled(self) -> bool:
        return self.get("rss.scheduler_enabled", "ENABLE_RSS_SCHEDULER", True, bool)

    @property
    def rss_scheduler_interval(self) -> int:
        return self.get("rss.scheduler_interval", "RSS_SCHEDULER_INTERVAL", 3600, int)
    
    # --- Crawler Config ---
    @property
    def crawler_min_title_length(self) -> int:
        return self.get("crawler.min_title_length", "CRAWLER_MIN_TITLE_LENGTH", 24, int)
    
    @property
    def crawler_retry_attempts(self) -> int:
        return self.get("crawler.retry.attempts", "CRAWLER_RETRY_ATTEMPTS", 3, int)
    
    @property
    def crawler_retry_wait_multiplier(self) -> int:
        return self.get("crawler.retry.wait_multiplier", "CRAWLER_RETRY_WAIT_MULTIPLIER", 1, int)
    
    @property
    def crawler_retry_wait_min(self) -> int:
        return self.get("crawler.retry.wait_min_seconds", "CRAWLER_RETRY_WAIT_MIN_SECONDS", 4, int)
    
    @property
    def crawler_retry_wait_max(self) -> int:
        return self.get("crawler.retry.wait_max_seconds", "CRAWLER_RETRY_WAIT_MAX_SECONDS", 10, int)
    
    @property
    def crawler_markdown_link_pattern(self) -> str:
        return self.get("crawler.parse.markdown_link_pattern", "CRAWLER_MARKDOWN_LINK_PATTERN", r"\[(.*?)\]\((.*?)\)", str)
    
    def crawler_ignore_image_links(self) -> bool:
        return self.get("crawler.parse.ignore_image_links", "CRAWLER_IGNORE_IMAGE_LINKS", True, bool)
    
    def crawler_require_https(self) -> bool:
        return self.get("crawler.url.require_https", "CRAWLER_REQUIRE_HTTPS", False, bool)

    @property
    def crawler_default_url(self) -> str:
        return self.get("crawler.url.default_url", "CRAWLER_DEFAULT_URL", "https://syncedreview.com/", str)
    
    # --- Puppeteer Config ---
    @property
    def puppeteer_browser_url(self) -> str:
        return self.get("puppeteer.browser_url", "PUPPETEER_BROWSER_URL", "http://localhost:9222", str)
    
    @property
    def puppeteer_viewport_width(self) -> int:
        return self.get("puppeteer.viewport.width", "PUPPETEER_VIEWPORT_WIDTH", 1920, int)
    
    @property
    def puppeteer_viewport_height(self) -> int:
        return self.get("puppeteer.viewport.height", "PUPPETEER_VIEWPORT_HEIGHT", 1080, int)
    
    @property
    def puppeteer_device_scale_factor(self) -> int:
        return self.get("puppeteer.viewport.device_scale_factor", "PUPPETEER_DEVICE_SCALE_FACTOR", 2, int)

    # --- Startup Lifecycle Config ---
    def is_startup_init_database_enabled(self) -> bool:
        return self.get("startup.init_database", "INIT_DATABASE", True, bool)
    
    def is_startup_init_rss_enabled(self) -> bool:
        return self.get("startup.init_rss_system", "INIT_RSS_SYSTEM", True, bool)

    # --- Middleware Config ---
    def is_auth_middleware_enabled(self) -> bool:
        return self.get("middleware.auth.enabled", "ENABLE_AUTH_MIDDLEWARE", False, bool)

    @property
    def auth_token(self) -> str:
        return self.get("middleware.auth.token", "API_X_TOKEN", "", str)

    # --- Module Execution Config ---
    @property
    def module_allowlist(self) -> List[str]:
        val = self.get("module.allowlist", "MODULE_EXEC_ALLOWLIST", ["*"], list)
        if isinstance(val, str):
            if val == "*":
                return ["*"]
            return [item.strip() for item in val.split(',') if item.strip()]
        return val

    # --- Ollama Config ---
    @property
    def ollama_url(self) -> str:
        return self.get("ollama.url", "OLLAMA_URL", "http://localhost:11434", str)
    
    @property
    def ollama_auth(self) -> str:
        return self.get("ollama.auth", "OLLAMA_AUTH", "", str)

    @property
    def logging_level(self) -> str:
        return self.get("logging.level", "LOG_LEVEL", "info", str)
    
    @property
    def logging_format(self) -> str:
        return self.get("logging.format", "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s", str)
    
    @property
    def logging_datefmt(self) -> str:
        return self.get("logging.datefmt", "LOG_DATEFMT", "%Y-%m-%d %H:%M:%S", str)
    
    @property
    def logging_propagate_uvicorn(self) -> bool:
        return self.get("logging.propagate_uvicorn", "LOG_PROPAGATE_UVICORN", False, bool)

    def get_logging_level_value(self) -> int:
        level = (self.logging_level or "").lower()
        if level == "debug":
            return logging.DEBUG
        if level == "warning":
            return logging.WARNING
        if level == "error":
            return logging.ERROR
        if level == "critical":
            return logging.CRITICAL
        return logging.INFO
# 创建全局配置实例
settings = Config()
# 保持向后兼容
_config_instance = settings

