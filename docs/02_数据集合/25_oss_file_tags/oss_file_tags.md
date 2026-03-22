# oss_file_tags 集合

存储文件标签信息，用于文件分类和检索。

## 主要用途

- 管理文件标签分类
- 支持多标签关联
- 便于文件按标签检索

## 配置项

- `collection.oss_file_tags` - 集合名称配置

## 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `_id` | ObjectId | 主键 ID |
| `file_id` | ObjectId | 关联的文件 ID |
| `tag_name` | string | 标签名称 |
| `created_at` | datetime | 创建时间 |
