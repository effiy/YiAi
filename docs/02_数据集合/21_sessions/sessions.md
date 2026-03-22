# sessions 集合

存储用户会话数据，用于维护用户状态和上下文信息。

## 主要用途

- 保存用户会话状态
- 存储用户上下文数据
- 支持多轮对话的会话连续性

## 配置项

- `collection.sessions` - 集合名称配置

## 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `_id` | ObjectId | 主键 ID |
| `user_id` | string | 用户 ID |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |
| `status` | string | 会话状态 |
