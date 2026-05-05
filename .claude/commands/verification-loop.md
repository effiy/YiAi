调用 `verification-loop` 技能执行验证循环。

```mermaid
graph TD
    A[/verification-loop] --> B[Phase 1: Environment snapshot]
    B --> C[Phase 2: Static preflight]
    C --> D{Blockers?}
    D -->|Yes| E[Fix → re-enter Phase 1]
    D -->|No| F[Phase 3: Environment alignment]
    F --> G[Phase 4: Single execution]
    G --> H{Pass?}
    H -->|Yes| I[Report success]
    H -->|No| J[Output one-shot fix list]
```

参数: `$ARGUMENTS`

执行要求：
- Phase 1–3 有阻塞项时不得进入 Phase 4；命令名必须取自 `package.json` scripts，禁止硬编码。
- Phase 4 仅执行一次；失败时不得自动重试。提供"一次性修复清单"及重入阶段。
- 自动化降级必须标注 ⚠️；不得将降级结果展示为完全通过。
