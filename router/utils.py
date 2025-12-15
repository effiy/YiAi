"""路由层公共工具：减少重复代码（如 get_user_id）并保持行为一致。"""

from typing import Optional
from fastapi import Request


def get_user_id(request: Request, user_id: Optional[str] = None, default: str = "default_user") -> str:
    """获取用户ID，优先级：参数 > X-User 请求头 > 默认值

    说明：
    - 各路由可通过 default 参数保留历史默认值（例如 prompt 路由曾使用 'bigboom'）。
    """
    if user_id:
        return user_id

    x_user = request.headers.get("X-User", "")
    if x_user:
        return x_user

    return default


