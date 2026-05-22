> | v1.0.0 | 2026-05-22 | deepseek-v4-pro | 🌿 feat/ci-cd-pipeline | 📎 故事任务 §5 AC

> **导航**: [← YiAi-技术评审](./YiAi-技术评审.md) · [YiAi-安全审计 →](./YiAi-安全审计.md)

> **来源引用**: 基于 YiAi-故事任务 §5 AC# + YiAi-使用场景 3 个场景 + YiAi-技术评审 CI/Docker/Compose 设计。证据 Level B。

[§0 基线溯源](#sec0-trace) · [§1 测试范围](#sec1-scope) · [§2 测试用例](#sec2-cases) · [§3 Gate A 交接信号](#sec3-gate-a)

---

### §0 基线溯源

| 溯源目标 | 映射关系 |
|---------|---------|
| 故事任务 AC1 | §2.1 TC-CI-01 — CI 配置存在性验证 |
| 故事任务 AC2 | §2.1 TC-CI-02 — CI 触发验证 |
| 故事任务 AC3 | §2.2 TC-DKR-01 — Docker 构建验证 |
| 故事任务 AC4 | §2.2 TC-DKR-02 — .dockerignore 排除验证 |
| 故事任务 AC5 | §2.3 TC-CMP-01 — Compose 启动验证 |
| 故事任务 AC6 | §2.4 TC-SEC-01 — 敏感信息泄漏检查 |
| 场景 1：推送检查 | §2.1 TC-CI-01, TC-CI-02 |
| 场景 2：镜像构建 | §2.2 TC-DKR-01, TC-DKR-02 |
| 场景 3：本地开发 | §2.3 TC-CMP-01 |

### 主要价值

- 🎯 Gate A 三关 — TC-CI-01 配置验证、TC-DKR-01 构建验证、TC-SEC-01 泄漏检查，全部通过方可进入实现
- 🔬 四类用例全覆盖 — 正常(5) + 边界(1) + 异常(2) + 回归(1)，共 9 个测试用例
- 📎 双基线对齐 — 用例溯源到故事任务 AC# 和使用场景，覆盖矩阵完整
- 🚦 交接信号可执行 — 每个 P0 用例附带可复制运行的验证命令

---

<a id="sec1-scope"></a>

## §1 测试范围

| 模块 | 测试类型 | 文件 | 关联 FP# |
|------|---------|------|---------|
| CI 流水线 | 配置验证 + 语法检查 | `.github/workflows/ci.yml` | FP1, FP2, FP3 |
| Docker 镜像 | 构建验证 + 内容审计 | `Dockerfile`, `.dockerignore` | FP4, FP5 |
| Docker Compose | 集成验证 | `docker-compose.yml` | FP6 |
| 安全 | 泄漏检查 | 全部新增文件 | R4 |

---

<a id="sec2-cases"></a>

## §2 测试用例

### §2.1 CI 流水线

#### TC-CI-01 — CI 配置文件存在且语法正确

| 属性 | 内容 |
|------|------|
| **类型** | 正常 |
| **Given** | 项目根目录有 `.github/workflows/ci.yml` |
| **When** | 用 GitHub Actions 校验器检查语法 |
| **Then** | 文件包含 `on: push/pull_request` 触发器、`python-version: "3.10"`、`flake8` 和 `pytest` 步骤 |

#### TC-CI-02 — CI 工作流步骤顺序正确

| 属性 | 内容 |
|------|------|
| **类型** | 正常 |
| **Given** | `.github/workflows/ci.yml` 存在 |
| **When** | 检查 job steps 顺序 |
| **Then** | 顺序为 checkout → setup-python → cache → install → lint → test |

#### TC-CI-03 — 缺少 requirements.txt 时的错误行为

| 属性 | 内容 |
|------|------|
| **类型** | 异常 |
| **Given** | requirements.txt 不存在或被重命名 |
| **When** | CI 运行 `pip install -r requirements.txt` |
| **Then** | 步骤失败，CI 标红，日志显示文件未找到 |

---

### §2.2 Docker 镜像

#### TC-DKR-01 — 镜像构建成功

| 属性 | 内容 |
|------|------|
| **类型** | 正常 |
| **Given** | Dockerfile 和 .dockerignore 存在于项目根目录 |
| **When** | 执行 `docker build -t yiai:test .` |
| **Then** | 构建退出码 0，镜像存在且大小 < 500MB |

#### TC-DKR-02 — .dockerignore 正确排除非必要文件

| 属性 | 内容 |
|------|------|
| **类型** | 正常 |
| **Given** | 镜像已构建 |
| **When** | 检查镜像内文件列表 `docker run --rm yiai:test ls /app` |
| **Then** | 不包含 `tests/`、`.git/`、`__pycache__/`、`docs/`、`*.pyc` 文件 |

#### TC-DKR-03 — 端口暴露正确

| 属性 | 内容 |
|------|------|
| **类型** | 边界 |
| **Given** | 镜像已构建 |
| **When** | 检查镜像元数据 `docker inspect yiai:test` |
| **Then** | `ExposedPorts` 包含 `10086/tcp` |

---

### §2.3 Docker Compose

#### TC-CMP-01 — 双服务启动成功

| 属性 | 内容 |
|------|------|
| **类型** | 正常 |
| **Given** | Dockerfile 和 docker-compose.yml 存在，Docker 环境可用 |
| **When** | 执行 `docker-compose up -d` |
| **Then** | `mongo` 和 `api` 两个容器均为 running 状态 |

#### TC-CMP-02 — API 服务响应正常

| 属性 | 内容 |
|------|------|
| **类型** | 正常 |
| **Given** | docker-compose 环境已启动 |
| **When** | 请求 `http://localhost:10086/docs` |
| **Then** | 返回 200，Swagger 文档页面可访问 |

#### TC-CMP-03 — MongoDB 未就绪时 API 的行为

| 属性 | 内容 |
|------|------|
| **类型** | 异常 |
| **Given** | MongoDB 容器延迟启动 |
| **When** | API 容器先于 MongoDB 就绪 |
| **Then** | API 启动失败或报错 MongoDB 连接不可达，重启后恢复 |

---

### §2.4 安全

#### TC-SEC-01 — 无明文敏感信息

| 属性 | 内容 |
|------|------|
| **类型** | 回归 |
| **Given** | 全部新增文件 |
| **When** | grep 搜索 `token`、`password`、`secret`、`key` 关键词 |
| **Then** | 命中仅出现在环境变量引用（如 `${API_X_TOKEN}`），无硬编码值 |

---

<a id="sec3-gate-a"></a>

## §3 Gate A 交接信号

| P0 用例 | 验证命令 | 预期 |
|---------|---------|------|
| TC-CI-01 | `grep -c "python-version\|flake8\|pytest" .github/workflows/ci.yml` | 全部命中 |
| TC-DKR-01 | `docker build -t yiai:test . 2>&1 \| tail -1` | `Successfully tagged yiai:test` |
| TC-SEC-01 | `grep -rE "(token\|password\|secret).*=.*[a-Z0-9]{8,}" .github/ Dockerfile docker-compose.yml 2>/dev/null \| grep -v "change-me\|CHANGE\|dev-"` | 无输出（无明文凭据） |

> **Gate A 通过标准**: 3 个 P0 用例全部通过后，方可进入 code 实现阶段。

---

### 变更记录

| 版本 | 日期 | 变更 | 触发 |
|------|------|------|------|
| v1.0.0 | 2026-05-22 | 初始生成 9 个测试用例，Gate A 3 个 P0 | /rui doc ci-cd-pipeline |
