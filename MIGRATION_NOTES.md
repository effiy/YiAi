# 静态文件迁移记录

## 迁移日期
2026-02-26

## 迁移内容
将 YiAi 项目的静态文件迁移到独立的 YiKnowledge 仓库，实现静态资源的集中管理。

## 迁移详情

### 源位置
- 路径: `/var/www/YiAi/static`
- 大小: 5.6MB
- 文件数: 235 个

### 目标位置
- 路径: `/var/www/YiKnowledge/static`
- 仓库: YiKnowledge (独立 Git 仓库)

### 迁移的内容
```
static/
├── Claude_Code/        # 296KB - Claude Code 文档
├── DevOps/            # 2.0MB - DevOps 流程文档
├── effiy.cn/          # 8KB - 代码审查文档
├── tools/             # 20KB - 工具文档
├── uploads/           # 2.8MB - 用户上传文件 (13个文件)
├── zh.zlib.li/        # 524KB - Z-Library 资源
├── favicon.ico        # 16KB
└── index.html         # 487B
```

## 配置变更

### config.yaml
```yaml
# 修改前
static:
  base_dir: "./static"

# 修改后
static:
  base_dir: "/var/www/YiKnowledge/static"
```

### main.py
```python
# 修改前
app.mount("/static", StaticFiles(directory="static"), name="static")

# 修改后
static_dir = settings.static_base_dir
app.mount("/static", StaticFiles(directory=static_dir), name="static")
```

## Git 提交记录

### YiKnowledge 仓库
- `ad4953e` - feat: migrate static files from YiAi
- `1044603` - docs: add README for YiKnowledge repository

### YiAi 仓库
- `bf4147c` - feat: mount static files to /var/www/YiKnowledge

## 验证结果

✅ 所有文件已成功复制到 YiKnowledge
✅ 配置文件已更新
✅ Settings 加载正确 (`/var/www/YiKnowledge/static`)
✅ 目录结构完整
✅ Git 提交已完成

## 后续操作建议

1. **测试应用启动**
   ```bash
   cd /var/www/YiAi
   python main.py
   ```

2. **验证静态文件访问**
   - 访问: `http://localhost:8000/static/index.html`
   - 验证上传文件可访问

3. **清理原静态目录** (可选)
   ```bash
   # 备份后可删除
   cd /var/www/YiAi
   mv static static.backup
   ```

4. **推送到远程仓库**
   ```bash
   # YiKnowledge
   cd /var/www/YiKnowledge
   git push origin main
   
   # YiAi
   cd /var/www/YiAi
   git push origin main
   ```

## 注意事项

- 静态文件现在由 YiKnowledge 仓库管理
- 新增静态文件应提交到 YiKnowledge 仓库
- YiAi 项目通过配置引用 YiKnowledge 的静态目录
- 其他项目也可以共享使用 YiKnowledge 的静态资源

## 回滚方案

如需回滚到本地静态目录:

1. 恢复配置文件
   ```bash
   cd /var/www/YiAi
   git revert bf4147c
   ```

2. 恢复静态目录
   ```bash
   mv static.backup static
   ```

## 相关文档

- YiKnowledge README: `/var/www/YiKnowledge/README.md`
- YiAi 配置文档: `/var/www/YiAi/config.yaml`
