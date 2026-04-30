---
paths:
  - "docs/周报/**/*.md"
---

# 周报（weekly）命令规范

> 核心原则、审查门禁、通知要求以 `../SKILL.md` 为准；本文件只承载 weekly 专属行为细节。

## 调用方式

```bash
/generate-document weekly                           # 本周周报
/generate-document weekly 2026-04-29                # 按给定日期归入其自然周
/generate-document weekly 2026-04-27~2026-05-03     # 按自然周起止
```

## 产出

- 路径：`docs/周报/<YYYY-MM-DD>~<YYYY-MM-DD>/周报.md`
- 更新机制：同周覆盖更新，版本号次版本 `+1`

## 工作流

**一次执行到底（强制）**：周报生成必须单轮完成，不得因任何非阻断原因中断。缺失信息写"待确认"继续推进；仅命中 H1-H4 阻断门槛时才允许打断。详见 [orchestration.md §4](../orchestration.md#4-阻断点)。

1. 确定覆盖周期：根据参数归算到自然周（周一至周日）
2. 动态上下文读取：执行 `collect-weekly-kpi.js --with-logs`、读取项目基础文件、编排日志、已有文档集
3. 生成周报：严格按 `rules/周报.md` 结构输出
4. Mermaid 审查：调用 `doc-mermaid-expert` 审查并写回
5. 自检：加载 `checklists/周报.md`，P0 全部通过才保存为通过状态
6. 保存：写入 `docs/周报/<自然周>/周报.md`
7. 步骤 6：先 `import-docs`，再 `wework-bot`

## 覆盖周期计算规则（自然周）

- 周一为起始日，周日为结束日
- 文件名与标题统一使用起止日期：`YYYY-MM-DD~YYYY-MM-DD`
- 给定日期自动展开为该自然周起止
- 起始~结束需校验起始为周一、结束为周日，不满足则按自然周重算