# chat_records 集合

存储用户与 AI 的对话历史记录。

## 主要用途

- 保存聊天消息历史
- 记录用户和 AI 的交互内容
- 支持对话回溯和历史查询

## 配置项

- `collection.chat_records` - 集合名称配置

## 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `_id` | ObjectId | 主键 ID |
| `session_id` | ObjectId | 关联的会话 ID |
| `role` | string | 消息角色（user/assistant） |
| `content` | string | 消息内容 |
| `created_at` | datetime | 创建时间 |
| `model` | string | 使用的模型 |
