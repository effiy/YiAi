# RSS 源管理

提供自动化的 RSS 源内容抓取和管理功能。

---

## 主要特性

- **定时抓取**：可配置的自动抓取调度器
- **灵活间隔**：支持自定义抓取间隔（秒）
- **多源管理**：同时管理多个 RSS 源
- **数据持久化**：文章内容存储到 MongoDB 数据库
- **生命周期管理**：应用启动时自动启动调度器，关闭时优雅停止

---

## 配置项

- `rss.scheduler_enabled` - 是否启用 RSS 调度器
- `rss.scheduler_interval` - 抓取间隔（秒）

---

## 相关文件

- `src/services/rss/scheduler.py` - RSS 调度器
- `src/services/rss/parser.py` - RSS 解析器
