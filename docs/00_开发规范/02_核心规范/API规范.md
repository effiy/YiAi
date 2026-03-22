# API 规范

本文档定义 YiAi 项目的 API 设计和开发规范。

---

## RESTful 设计原则

### 使用正确的 HTTP 方法

| 方法 | 用途 | 幂等 |
|------|------|------|
| GET | 获取资源 | ✅ |
| POST | 创建资源 | ❌ |
| PUT | 完整更新资源 | ✅ |
| PATCH | 部分更新资源 | ❌ |
| DELETE | 删除资源 | ✅ |

### 资源命名

使用名词复数形式，使用小写字母和连字符：

```
# 正确示例
GET    /users              # 获取用户列表
GET    /users/{id}         # 获取单个用户
POST   /users              # 创建用户
PUT    /users/{id}         # 更新用户
DELETE /users/{id}         # 删除用户

# 避免示例
GET    /getUsers
POST   /createUser
GET    /UserList
```

### 层级资源

使用斜杠表示层级关系：

```
GET /users/{user_id}/orders          # 获取用户的订单列表
GET /users/{user_id}/orders/{order_id} # 获取用户的单个订单
```

---

## 请求规范

### 请求参数

#### 路径参数

用于资源标识：

```python
@router.get("/users/{user_id}")
async def get_user(user_id: str):
    pass
```

#### 查询参数

用于过滤、排序、分页等：

```python
@router.get("/users")
async def list_users(
    page: int = 1,
    size: int = 20,
    keyword: Optional[str] = None
):
    pass
```

#### 请求体

用于创建和更新资源：

```python
@router.post("/users")
async def create_user(request: UserCreateRequest):
    pass
```

### 参数验证

使用 Pydantic 进行严格验证：

```python
from pydantic import BaseModel, Field, EmailStr

class UserCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="用户姓名"
    )
    email: EmailStr = Field(..., description="邮箱地址")
    age: int = Field(
        ...,
        ge=0,
        le=150,
        description="年龄"
    )
```

---

## 响应规范

### 统一响应格式

所有 API 响应必须使用统一格式：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

#### 成功响应

```python
from core.response import success

# 基本成功响应
return success(data=user_data)

# 带消息的成功响应
return success(data=user_data, message="创建成功")
```

#### 错误响应

```python
from core.response import error
from core.error_codes import ErrorCode

# 业务错误
return error(code=ErrorCode.NOT_FOUND, message="用户不存在")

# 参数错误
return error(code=ErrorCode.INVALID_PARAMS, message="参数无效")
```

### HTTP 状态码

| 状态码 | 用途 |
|--------|------|
| 200 | 请求成功 |
| 201 | 资源创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## API 文档

### 使用 FastAPI 自动文档

FastAPI 自动生成 Swagger UI 和 ReDoc：

- Swagger UI: `/docs`
- ReDoc: `/redoc`

### 端点文档

每个端点都应该有清晰的文档字符串：

```python
@router.post("/users", summary="创建用户", description="创建一个新用户")
async def create_user(
    request: UserCreateRequest,
):
    """
    创建用户接口。

    Args:
        request: 用户创建请求数据

    Returns:
        创建的用户信息

    Raises:
        BusinessException: 用户已存在时抛出
    """
    pass
```

---

## 分页规范

### 请求参数

```python
@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量")
):
    pass
```

### 响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "size": 20
  }
}
```

---

## 版本管理

### API 版本

在 URL 中包含版本号：

```
/api/v1/users
/api/v2/users
```

---

## 相关规范

- [路由规范](./路由规范.md)
- [编码规范](./编码规范.md)
- [文档规范](./文档规范.md)
