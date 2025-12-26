"""统一响应格式工具（已迁移到router.utils，保留此文件以兼容旧代码）"""
from router.utils import success_response, error_response, list_response

# 重新导出以保持向后兼容
__all__ = ['success_response', 'error_response', 'list_response']

