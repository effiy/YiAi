# Orchestration Overhaul — Project Report

> **Document Version**: v1.0 | **Last Updated**: 2026-05-03 | **Feature**: orchestration-overhaul
>

---

## Project Overview

Orchestration Overhaul 为 YiAi 引入确定性执行编排层，涵盖流水线引擎、Harness 评分、Launcher 抽象和 5 层循环防护。本文档记录项目范围、实际变更和验证结论。

---

## Scope

### Planned

- PipelineEngine DAG 执行引擎
- DAGValidator 环检测
- HarnessScorer 确定性评分
- BaseLauncher + DirectLauncher + SubprocessLauncher
- ModuleGraphTracker L4 调用图追踪
- Orchestration API 路由
- Launcher 健康端点扩展
- 配置集成

### Delivered

- 文档集 01-05, 07 已生成
- 代码实现：⏳ 待 implement-code 阶段完成

---

## Changed Files

### 新增文件 (12)

| # | File Path | Description |
|---|-----------|-------------|
| 1 | `src/services/orchestration/__init__.py` | 包初始化 |
| 2 | `src/services/orchestration/engine.py` | PipelineEngine |
| 3 | `src/services/orchestration/validator.py` | DAGValidator |
| 4 | `src/services/orchestration/harness.py` | HarnessScorer |
| 5 | `src/services/orchestration/launcher.py` | BaseLauncher + 实现 |
| 6 | `src/core/observer/tracker.py` | ModuleGraphTracker L4 |
| 7 | `src/api/routes/orchestration.py` | 流水线 API |
| 8 | `docs/orchestration-overhaul/01_requirement-document.md` | 需求文档 |
| 9 | `docs/orchestration-overhaul/02_requirement-tasks.md` | 需求任务 |
| 10 | `docs/orchestration-overhaul/03_design-document.md` | 设计文档 |
| 11 | `docs/orchestration-overhaul/04_usage-document.md` | 使用文档 |
| 12 | `docs/orchestration-overhaul/05_dynamic-checklist.md` | 动态清单 |

### 修改文件 (5)

| # | File Path | Description |
|---|-----------|-------------|
| 1 | `src/core/config.py` | 新增 orchestration_* 字段 |
| 2 | `src/main.py` | 注册 orchestration 路由 |
| 3 | `src/services/execution/executor.py` | 集成 Launcher + Tracker |
| 4 | `src/api/routes/observer_health.py` | 扩展 Launcher 健康状态 |
| 5 | `config.yaml` | 添加 orchestration 默认配置 |

---

## Verification Conclusion

| Item | Status | Evidence |
|------|--------|----------|
| 文档集完整性 | ✅ Passed | 01-05, 07 齐全 |
| 影响链闭合 | ✅ Passed | 03 Impact Analysis 所有 change point closed |
| P0 场景覆盖 | ✅ Passed | 02 含 S1/S2/S3/S4 四个 P0 场景 |
| 代码实现 | ⏳ Pending | 等待 implement-code 阶段 |
| 冒烟测试 | ⏳ Pending | 等待实现完成后执行 |

---

## Known Issues / Limitations

1. **SubprocessLauncher 未验证**：subprocess 模式在真实负载下的性能和稳定性待验证。
2. **Harness Rubric 单一**：默认评分标准可能不适用于所有模块类型，需后续支持自定义。
3. **Pipeline 状态内存存储**：当前设计假设 pipeline 状态在内存中，服务重启会丢失，需后续持久化到 MongoDB。

---

## Next Steps

1. 执行 `implement-code orchestration-overhaul` 完成代码实现
2. 补充单元测试和 E2E 测试
3. 在真实负载下验证 SubprocessLauncher
4. 为 `orchestration_pipelines` 集合添加 MongoDB 索引

---

## Postscript: Future Planning & Improvements

1. **Remote Worker Launcher**：Celery/RQ 远程派发模式。
2. **Pipeline Visualization**：自动生成 Mermaid 图。
3. **Adaptive Rubrics**：基于历史数据训练评分模型。
4. **Distributed Loop Detection**：Redis 共享 L4 调用图状态。
