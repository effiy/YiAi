"""数据模型定义 (Schemas)
- 包含所有 API 请求和响应的 Pydantic 模型
- 按功能模块组织：Module, RSS, etc.
"""
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field

# --- Module Schemas ---
class ExecuteRequest(BaseModel):
    """
    通用模块执行请求模型
    
    Example:
        {
            "module_name": "services.web.crawler.crawler_service",
            "method_name": "crawl_and_extract",
            "parameters": {"url": "https://example.com"}
        }
    """
    module_name: str = Field(default="services.web.crawler.crawler_service", description="目标模块全路径")
    method_name: str = Field(default="crawl_and_extract", description="目标函数名")
    parameters: Union[Dict[str, Any], str] = Field(
        default_factory=lambda: {"url": "https://www.qbitai.com/"},
        description="传递给目标函数的参数，支持字典或 JSON 字符串"
    )

    class Config:
        arbitrary_types_allowed = True

class FileUploadRequest(BaseModel):
    """
    文件上传请求模型 (JSON 方式)
    """
    filename: str = Field(..., description="文件名")
    content: str = Field(..., description="文件内容 (文本或 Base64 字符串)")
    is_base64: bool = Field(default=False, description="内容是否为 Base64 编码")
    target_dir: str = Field(default="static", description="目标存储目录")

class ImageUploadToOssRequest(BaseModel):
    data_url: str = Field(..., description="DataURL 或 Base64 字符串")
    filename: str = Field(default="image.png", description="文件名（含扩展名）")
    directory: str = Field(default="aicr", description="OSS 目录前缀")

class FolderDeleteRequest(BaseModel):
    """
    文件夹删除请求模型
    """
    target_dir: str = Field(..., description="要删除的目录路径")

class FileDeleteRequest(BaseModel):
    """
    文件删除请求模型
    """
    target_file: str = Field(..., description="要删除的文件路径")

class FileReadRequest(BaseModel):
    """
    文件读取请求模型
    """
    target_file: str = Field(..., description="要读取的文件路径")

class FileWriteRequest(BaseModel):
    """
    文件写入请求模型
    """
    target_file: str = Field(..., description="要写入的文件路径")
    content: str = Field(..., description="文件内容")
    is_base64: bool = Field(default=False, description="内容是否为 Base64 编码")

class FileRenameRequest(BaseModel):
    """
    文件重命名请求模型
    """
    old_path: str = Field(..., description="旧文件路径")
    new_path: str = Field(..., description="新文件路径")

class FolderRenameRequest(BaseModel):
    """
    文件夹重命名请求模型
    """
    old_dir: str = Field(..., description="旧目录路径")
    new_dir: str = Field(..., description="新目录路径")

# --- RSS Schemas ---
class ParseRssRequest(BaseModel):
    """
    解析单个 RSS 源请求
    
    Example:
        {
            "url": "https://example.com/rss.xml",
            "name": "Example RSS"
        }
    """
    url: str = Field(..., description="RSS 源 URL")
    name: Optional[str] = Field(None, description="自定义源名称，不填则自动获取")

class ParseAllRssRequest(BaseModel):
    """
    批量解析 RSS 请求
    
    Example:
        {
            "force": true
        }
    """
    force: Optional[bool] = Field(False, description="是否强制刷新")

class SchedulerConfigRequest(BaseModel):
    """
    RSS 调度器配置请求
    
    Example:
        {
            "enabled": true,
            "type": "interval",
            "interval": 3600
        }
    """
    enabled: Optional[bool] = Field(None, description="是否启用调度器")
    type: Optional[str] = Field(None, description="调度类型: interval 或 cron")
    interval: Optional[int] = Field(None, description="间隔时间(秒)，仅 interval 类型有效")
    cron: Optional[Dict[str, Any]] = Field(None, description="Cron 表达式配置，仅 cron 类型有效")

# --- WeWork Schemas ---
class WeWorkWebhookRequest(BaseModel):
    """
    企业微信机器人 Webhook 请求模型
    
    Example:
        {
            "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
            "content": "要发送的消息内容"
        }
    """
    webhook_url: str = Field(..., description="企业微信机器人 Webhook URL")
    content: str = Field(..., description="要发送的消息内容")
