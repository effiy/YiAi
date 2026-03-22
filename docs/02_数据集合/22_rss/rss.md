# rss 集合

存储从 RSS 源抓取的文章内容。

## 主要用途

- 保存 RSS 源文章数据
- 存储文章标题、内容、发布时间等元数据
- 支持文章检索和管理

## 配置项

- `collection.rss` - 集合名称配置

## 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `_id` | ObjectId | 主键 ID |
| `title` | string | 文章标题 |
| `link` | string | 文章链接 |
| `source` | string | 来源标识 |
| `published_at` | datetime | 发布时间 |
| `summary` | string | 文章摘要 |
| `content` | string | 文章内容 |
| `fetched_at` | datetime | 抓取时间 |
