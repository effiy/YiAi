import os
import yaml
from typing import List, Union, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource

class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """
    A simple settings source that reads from a config.yaml file.
    It flattens the nested YAML structure to match the flat settings fields.
    e.g., {"server": {"host": "..."}} -> {"server_host": "..."}
    """
    def get_field_value(
        self, field: Field, field_name: str
    ) -> tuple[Any, str, bool]:
        encoding = self.config.get('env_file_encoding')
        return None, field_name, False

    def _flatten(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def __call__(self) -> Dict[str, Any]:
        config_file = "config.yaml"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                return self._flatten(data)
        return {}

class Settings(BaseSettings):
    # Server
    server_host: str = Field("0.0.0.0", validation_alias="host")
    server_port: int = Field(8000, validation_alias="port")
    server_reload: bool = Field(True, validation_alias="uvicorn_reload")
    uvicorn_limit_concurrency: int = Field(1000, validation_alias="uvicorn_limit_concurrency")
    uvicorn_limit_max_requests: int = Field(10000, validation_alias="uvicorn_limit_max_requests")
    uvicorn_timeout_keep_alive: int = Field(5, validation_alias="uvicorn_timeout_keep_alive")
    
    # CORS
    cors_origins: Union[str, List[str]] = Field(["*"], validation_alias="cors_origins")
    cors_allow_any_origin: bool = Field(True, validation_alias="cors_allow_any_origin")

    # Pagination
    pagination_default_size: int = Field(2000, validation_alias="default_page_size")
    pagination_max_size: int = Field(8000, validation_alias="max_page_size")
    pagination_min_size: int = Field(1, validation_alias="min_page_size")

    # User
    default_user_id: str = Field("default_user", validation_alias="default_user_id")

    # Static
    static_base_dir: str = Field("./static", validation_alias="static_base_dir")
    static_max_zip_size_mb: int = Field(100, validation_alias="static_max_zip_size_mb")

    # Database
    mongodb_url: str = Field("mongodb://localhost:27017", validation_alias="mongodb_url")
    mongodb_db_name: str = Field("yi_ai", validation_alias="mongodb_database")
    mongodb_pool_size: int = Field(10, validation_alias="mongodb_pool_size")
    mongodb_max_pool_size: int = Field(50, validation_alias="mongodb_max_pool_size")
    
    collection_sessions: str = Field("sessions", validation_alias="collection_sessions")
    collection_rss: str = Field("rss", validation_alias="collection_rss")
    collection_chat_records: str = Field("chat_records", validation_alias="collection_chat_records")
    collection_pet_data_sync: str = Field("pet_data_sync", validation_alias="collection_pet_data_sync")
    collection_seeds: str = Field("seeds", validation_alias="collection_seeds")
    collection_oss_file_tags: str = Field("oss_file_tags", validation_alias="collection_oss_file_tags")
    collection_oss_file_info: str = Field("oss_file_info", validation_alias="collection_oss_file_info")

    # OSS
    oss_access_key: str = Field("", validation_alias="oss_access_key_id")
    oss_secret_key: str = Field("", validation_alias="oss_access_key_secret")
    oss_endpoint: str = Field("", validation_alias="oss_endpoint")
    oss_bucket: str = Field("", validation_alias="oss_bucket_name")
    oss_domain: str = Field("", validation_alias="oss_domain")
    oss_max_file_size_mb: int = Field(50, validation_alias="oss_max_file_size")
    oss_allowed_extensions: List[str] = Field(
        [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".epub", ".md"],
        validation_alias="oss_allowed_extensions"
    )

    # RSS
    rss_scheduler_enabled: bool = Field(True, validation_alias="enable_rss_scheduler")
    rss_scheduler_interval: int = Field(3600, validation_alias="rss_scheduler_interval")

    # Crawler
    crawler_min_title_length: int = Field(24, validation_alias="crawler_min_title_length")
    crawler_retry_attempts: int = Field(3, validation_alias="crawler_retry_attempts")
    crawler_retry_wait_multiplier: int = Field(1, validation_alias="crawler_retry_wait_multiplier")
    crawler_retry_wait_min_seconds: int = Field(4, validation_alias="crawler_retry_wait_min_seconds")
    crawler_retry_wait_max_seconds: int = Field(10, validation_alias="crawler_retry_wait_max_seconds")
    crawler_markdown_link_pattern: str = Field(r"\[(.*?)\]\((.*?)\)", validation_alias="crawler_markdown_link_pattern")
    crawler_ignore_image_links: bool = Field(True, validation_alias="crawler_ignore_image_links")
    crawler_require_https: bool = Field(False, validation_alias="crawler_require_https")
    crawler_default_url: str = Field("https://syncedreview.com/", validation_alias="crawler_default_url")

    # Puppeteer
    puppeteer_browser_url: str = Field("http://localhost:9222", validation_alias="puppeteer_browser_url")
    puppeteer_viewport_width: int = Field(1920, validation_alias="puppeteer_viewport_width")
    puppeteer_viewport_height: int = Field(1080, validation_alias="puppeteer_viewport_height")
    puppeteer_device_scale_factor: int = Field(2, validation_alias="puppeteer_device_scale_factor")

    # Startup
    startup_init_database: bool = Field(True, validation_alias="init_database")
    startup_init_rss_system: bool = Field(True, validation_alias="init_rss_system")

    # Middleware
    middleware_auth_enabled: bool = Field(False, validation_alias="enable_auth_middleware")
    middleware_auth_token: str = Field("", validation_alias="api_x_token")

    # Module
    module_allowlist: Union[str, List[str]] = Field(["*"], validation_alias="module_exec_allowlist")

    # Ollama
    ollama_url: str = Field("http://localhost:11434", validation_alias="ollama_url")
    ollama_auth: str = Field("", validation_alias="ollama_auth")

    # Logging
    logging_level: str = Field("INFO", validation_alias="log_level")
    logging_format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", validation_alias="log_format")
    logging_datefmt: str = Field("%Y-%m-%d %H:%M:%S", validation_alias="log_datefmt")
    logging_propagate_uvicorn: bool = Field(False, validation_alias="log_propagate_uvicorn")
    
    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            YamlConfigSettingsSource(settings_cls),
        )

    @property
    def static_max_zip_size(self) -> int:
        return self.static_max_zip_size_mb * 1024 * 1024

    @property
    def oss_max_file_size(self) -> int:
        return self.oss_max_file_size_mb * 1024 * 1024
    
    def get_cors_origins(self) -> List[str]:
        if isinstance(self.cors_origins, str) and self.cors_origins == "*":
            return ["*"]
        if isinstance(self.cors_origins, str):
             return [item.strip() for item in self.cors_origins.split(',') if item.strip()]
        return self.cors_origins

    # Compat methods
    def is_startup_init_database_enabled(self) -> bool: return self.startup_init_database
    def is_startup_init_rss_enabled(self) -> bool: return self.startup_init_rss_system
    def is_rss_scheduler_enabled(self) -> bool: return self.rss_scheduler_enabled
    def is_auth_middleware_enabled(self) -> bool: return self.middleware_auth_enabled
    
    @property
    def auth_token(self) -> str: return self.middleware_auth_token
    
    @property
    def crawler_retry_wait_min(self) -> int: return self.crawler_retry_wait_min_seconds
    
    @property
    def crawler_retry_wait_max(self) -> int: return self.crawler_retry_wait_max_seconds

settings = Settings()
