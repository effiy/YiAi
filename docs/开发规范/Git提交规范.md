# Git 提交规范

本文档定义 YiAi 项目的 Git 提交规范。

---

## 提交消息格式

### 规范格式

提交消息使用以下格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

其中：
- `type` - 提交类型（必需）
- `scope` - 影响范围（可选）
- `subject` - 简短描述（必需，不超过 50 字符）
- `body` - 详细描述（可选）
- `footer` - 关联 Issue 或 BREAKING CHANGE（可选）

### 示例

```
feat(auth): 添加用户登录功能

- 实现用户名密码登录
- 添加 JWT token 生成
- 增加登录日志记录

Closes #123
```

---

## 提交类型 (Type)

### 功能相关

| 类型 | 描述 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 bug |
| `refactor` | 重构（既不是新增功能，也不是修复 bug） |
| `perf` | 性能优化 |

### 文档和样式

| 类型 | 描述 |
|------|------|
| `docs` | 文档更新 |
| `style` | 代码格式调整（不影响代码运行） |

### 构建和工具

| 类型 | 描述 |
|------|------|
| `build` | 构建系统或外部依赖的变动 |
| `ci` | CI/CD 配置变动 |
| `chore` | 其他不修改 src 或 test 的变动 |

### 测试

| 类型 | 描述 |
|------|------|
| `test` | 测试相关变动 |

---

## 影响范围 (Scope)

### 常用范围

| 范围 | 描述 |
|------|------|
| `api` | API 相关 |
| `auth` | 认证相关 |
| `db` | 数据库相关 |
| `config` | 配置相关 |
| `docs` | 文档相关 |
| `upload` | 上传相关 |
| `rss` | RSS 相关 |
| `ai` | AI 相关 |

### 示例

```
feat(api): 添加新的 API 端点
fix(auth): 修复 token 验证
refactor(db): 重构数据库访问层
docs(readme): 更新 README 文档
```

---

## 简短描述 (Subject)

### 规范

- 使用祈使句，现在时态
- 首字母小写
- 结尾不加句号
- 不超过 50 字符

### 示例

```
# 正确示例
feat(auth): 添加用户登录功能
fix(api): 修复参数验证错误
refactor(db): 重构查询方法

# 避免示例
feat(auth): 添加了用户登录功能
fix(api): 修复了参数验证错误
refactor(db): 重构查询方法。
```

---

## 详细描述 (Body)

### 规范

- 解释为什么做这个变更
- 描述变更的内容
- 使用项目符号列表
- 每行不超过 72 字符

### 示例

```
feat(upload): 添加图片压缩功能

- 支持 JPG/PNG 图片压缩
- 可配置压缩质量
- 添加压缩前后的大小日志
- 更新相关文档
```

---

## 页脚 (Footer)

### 关联 Issue

使用 `Closes`、`Fixes`、`Resolves` 关联 Issue：

```
fix(auth): 修复登录超时问题

- 增加超时时间配置
- 优化重试逻辑

Closes #123
Fixes #456
```

### 破坏性变更

使用 `BREAKING CHANGE:` 标记破坏性变更：

```
refactor(api): 重构响应格式

BREAKING CHANGE: 响应格式从 {result: ...} 改为 {code: ..., data: ...}

需要更新所有调用方的代码以适配新格式。
```

---

## 实际示例

### 新功能

```
feat(rss): 添加 RSS 源管理功能

- 实现 RSS 源 CRUD 操作
- 添加定时抓取调度器
- 支持多源同时抓取
- 数据存储到 MongoDB

Closes #23
```

### Bug 修复

```
fix(upload): 修复文件名处理问题

- 修复中文文件名乱码
- 增加文件名安全检查
- 添加扩展名验证

Fixes #42
```

### 文档更新

```
docs(readme): 更新安装说明

- 添加 Docker 安装方式
- 更新依赖列表
- 补充配置说明
```

### 重构

```
refactor(db): 统一数据库访问方法

- 创建统一的 CRUD 接口
- 移除重复代码
- 添加类型注解

BREAKING CHANGE: 所有数据库调用需要使用新接口
```

### 性能优化

```
perf(api): 优化查询性能

- 添加数据库索引
- 实现查询结果缓存
- 减少 N+1 查询

性能提升约 40%
```

---

## 提交频率

### 原子提交

每次提交只包含一个逻辑变更：

```bash
# 正确示例
git commit -m "feat(api): 添加用户列表接口"
git commit -m "docs: 添加 API 文档"
git commit -m "test: 添加用户接口测试"

# 避免示例
git commit -m "完成用户管理模块"
```

### 及时提交

不要积累太多变更：

```bash
# 推荐 - 小步提交
git add src/api/users.py
git commit -m "feat(api): 添加用户创建接口"

git add src/services/user_service.py
git commit -m "feat(api): 实现用户服务逻辑"
```

---

## 分支管理

### 分支命名

```
# 功能分支
feature/user-login
feature/rss-management

# 修复分支
fix/login-bug
fix/upload-error

# 发布分支
release/v1.0.0
release/v1.1.0

# 热修复分支
hotfix/critical-bug
hotfix/security-patch
```

---

## Git 钩子

### 提交前检查

建议使用 pre-commit 钩子：

```bash
# .pre-commit-config.yaml 示例
repos:
- repo: https://github.com/psf/black
  rev: 23.10.1
  hooks:
  - id: black

- repo: https://github.com/pycqa/isort
  rev: 5.12.0
  hooks:
  - id: isort
```

---

## 相关规范

- [编码规范](./编码规范.md)
- [文档规范](./文档规范.md)
