# oss_file_info 集合

存储上传文件的元数据信息。

## 主要用途

- 保存文件基本信息（文件名、大小、类型等）
- 记录文件存储路径和访问 URL
- 关联文件标签和描述信息

## 配置项

- `collection.oss_file_info` - 集合名称配置

## 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `_id` | ObjectId | 主键 ID |
| `filename` | string | 原始文件名 |
| `object_name` | string | 存储对象名称 |
| `url` | string | 访问 URL |
| `file_type` | string | 文件类型 |
| `file_size` | int | 文件大小（字节） |
| `uploader` | string | 上传者标识 |
| `created_at` | datetime | 上传时间 |
