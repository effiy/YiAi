# Orchestration Overhaul — Usage Document

> **Document Version**: v1.0 | **Last Updated**: 2026-05-03 | **Upstream**: [03 Design Document](./03_design-document.md)
>

[Quick Start](#quick-start) | [Good Scenarios](#good-scenarios) | [Bad Scenarios / Anti-patterns](#bad-scenarios--anti-patterns) | [Configuration](#configuration) | [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Enable Orchestration

Ensure `config.yaml` contains the orchestration section:

```yaml
observer:
  enabled: true
  guard_enabled: true
  guard_max_depth: 3

orchestration:
  enabled: true
  launcher_mode: direct
  max_steps: 100
  step_timeout_seconds: 300
  harness_enabled: true
```

### 2. Submit Your First Pipeline

```bash
curl -X POST http://localhost:8000/orchestration/pipelines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "rss-summary-pipeline",
    "steps": [
      {
        "id": "fetch",
        "module": "services.rss.rss_parser",
        "function": "parse_feed",
        "parameters": {"url": "https://example.com/rss.xml"}
      },
      {
        "id": "summarize",
        "module": "services.ai.summarizer",
        "function": "summarize",
        "parameters": {"text": "${fetch.output}"},
        "depends_on": ["fetch"]
      }
    ]
  }'
```

Expected response:

```json
{
  "pipeline_id": "pipe_20260503_001",
  "status": "created",
  "steps": 2
}
```

### 3. Run the Pipeline

```bash
curl -X POST http://localhost:8000/orchestration/pipelines/pipe_20260503_001/run
```

### 4. Check Status and Scores

```bash
# Pipeline status
curl http://localhost:8000/orchestration/pipelines/pipe_20260503_001/status

# Harness scores
curl "http://localhost:8000/state/records?record_type=audit_score&tags=pipe_20260503_001"
```

### 5. Switch Launcher Mode (Optional)

Edit `config.yaml`:

```yaml
orchestration:
  launcher_mode: subprocess
```

Restart the server and verify:

```bash
curl http://localhost:8000/health/launcher
```

---

## Good Scenarios

### Scenario 1: Multi-Step Data Processing Pipeline

📋 **Background**: You need to fetch data, transform it, and store the result.

🎨 **Operation**:

```bash
curl -X POST http://localhost:8000/orchestration/pipelines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "etl-pipeline",
    "steps": [
      {"id": "extract", "module": "my_modules.extract", "function": "fetch_data", "parameters": {"source": "api"}},
      {"id": "transform", "module": "my_modules.transform", "function": "clean_data", "parameters": {"input": "${extract.output}"}, "depends_on": ["extract"]},
      {"id": "load", "module": "my_modules.load", "function": "save_to_db", "parameters": {"data": "${transform.output}"}, "depends_on": ["transform"]}
    ]
  }'
```

📋 **Result**: Steps execute in order (extract → transform → load). Each step output feeds the next. Harness scores each step.

✅ **Why it is good**: Clear dependency chain, single API submission, observable intermediate states.

---

### Scenario 2: Parallel Branch Execution

📋 **Background**: Two independent tasks can run in parallel, then merge.

🎨 **Operation**:

```bash
curl -X POST http://localhost:8000/orchestration/pipelines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "parallel-branch",
    "steps": [
      {"id": "task_a", "module": "mod_a", "function": "run"},
      {"id": "task_b", "module": "mod_b", "function": "run"},
      {"id": "merge", "module": "mod_merge", "function": "combine", "parameters": {"a": "${task_a.output}", "b": "${task_b.output}"}, "depends_on": ["task_a", "task_b"]}
    ]
  }'
```

📋 **Result**: `task_a` and `task_b` execute concurrently. `merge` waits for both.

✅ **Why it is good**: Proper use of DAG semantics to express parallelism; no manual coordination needed.

---

### Scenario 3: Switching to Subprocess for Untrusted Code

📋 **Background**: You want to execute third-party modules in isolation.

🎨 **Operation**:

1. Update `config.yaml`:
   ```yaml
   orchestration:
     launcher_mode: subprocess
   ```
2. Restart server.
3. Submit and run pipelines normally — no API changes required.

📋 **Result**: All module executions run in separate python3 subprocesses.

✅ **Why it is good**: Security hardening with zero code change; launcher abstraction hides complexity.

---

### Scenario 4: Querying Harness Scores for Quality Monitoring

📋 **Background**: You want to track module quality over time.

🎨 **Operation**:

```bash
curl "http://localhost:8000/state/records?record_type=audit_score&page_size=100"
```

📋 **Result**: List of audit score records with pipeline_id, step_id, score (0-100), and timestamp.

✅ **Why it is good**: Scores are deterministic and persistent, enabling trend analysis and regression detection.

---

## Bad Scenarios / Anti-patterns

### Scenario 1: Creating a Cyclic Pipeline

📋 **Background**: A user accidentally creates a dependency loop.

🎨 **Bad Operation**:

```bash
curl -X POST http://localhost:8000/orchestration/pipelines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "bad-cycle",
    "steps": [
      {"id": "a", "module": "mod", "function": "run", "depends_on": ["b"]},
      {"id": "b", "module": "mod", "function": "run", "depends_on": ["a"]}
    ]
  }'
```

📋 **Result**: `400 Bad Request` with message `Cycle detected: a -> b -> a`.

❌ **Why it is bad**: Cyclic dependencies make execution impossible. Always draw your dependency graph on paper before submitting.

---

### Scenario 2: Deep Recursive Module Calls

📋 **Background**: A module calls `/execution` back to itself without depth awareness.

🎨 **Bad Operation**:

Module `recursive_mod.py`:
```python
import requests

def run(params):
    # Calls back to the same endpoint, causing infinite recursion
    requests.get("http://localhost:8000/execution/?module_name=recursive_mod&method_name=run")
    return {"done": True}
```

📋 **Result**: After 3 levels (default guard depth), the request returns `508 Loop Detected`.

❌ **Why it is bad**: Recursive callbacks exhaust stack and connections. Design modules to be leaf nodes or use explicit pipeline steps instead of runtime callbacks.

---

### Scenario 3: Mixing Launcher Modes in the Same Request

📋 **Background**: A user attempts to force per-step launcher selection (not supported).

🎨 **Bad Operation**:

```bash
curl -X POST http://localhost:8000/orchestration/pipelines \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {"id": "trusted", "module": "mod", "function": "run", "launcher": "direct"},
      {"id": "untrusted", "module": "mod", "function": "run", "launcher": "subprocess"}
    ]
  }'
```

📋 **Result**: The `"launcher"` field in step definition is ignored. All steps use the global launcher mode.

❌ **Why it is bad**: Per-step launcher selection is not supported (P2). Trying to use it leads to confusion. Set launcher mode globally in `config.yaml`.

---

### Scenario 4: Ignoring Harness Score of Zero

📋 **Background**: A pipeline step throws an exception but the user ignores the score.

🎨 **Bad Operation**:

```bash
# Run pipeline
curl -X POST http://localhost:8000/orchestration/pipelines/my-pipe/run

# Never check scores
# Never check pipeline status
```

📋 **Result**: The pipeline may have failed silently at step 3, but the user assumes success because the HTTP response was 200.

❌ **Why it is bad**: Always check `pipeline.status` and `scores` after execution. A 200 response only means the orchestrator accepted the job, not that all steps succeeded.

**Correct approach**:

```bash
curl http://localhost:8000/orchestration/pipelines/my-pipe/status | jq '.steps[].score'
```

---

## Configuration

| Config Key | Default | Description |
|-----------|---------|-------------|
| `orchestration.enabled` | `true` | 启用编排服务 |
| `orchestration.launcher_mode` | `direct` | Launcher 模式：`direct` 或 `subprocess` |
| `orchestration.max_steps` | `100` | 单流水线最大步骤数 |
| `orchestration.step_timeout_seconds` | `300` | 单步骤超时（秒） |
| `orchestration.harness_enabled` | `true` | 启用 Harness 评分 |
| `orchestration.harness_default_rubric` | `default` | 默认评分标准 |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `400 Cycle detected` | 流水线定义含环 | 检查 `depends_on`，确保无循环依赖 |
| `508 Loop Detected` | 模块运行时递归调用 | 重构模块，使用流水线步骤替代运行时回调 |
| `429 Too Many Requests` | ThrottleMiddleware 触发 | 降低请求频率，或加入 throttle whitelist |
| `Launcher timeout` | SubprocessLauncher 超时 | 增加 `step_timeout_seconds` 或优化模块性能 |
| `Scores not saved` | State Store 未启用 | 确保 `state_store_enabled: true` |

---

## Postscript: Future Planning & Improvements

1. **Per-Step Launcher Selection**: Allow `"launcher": "subprocess"` in individual steps.
2. **Pipeline Templates**: Pre-built templates for common patterns (ETL, RSS→AI→Upload).
3. **Score Alerting**: Webhook notification when Harness score drops below threshold.
4. **Dry Run Mode**: Execute pipeline without side effects for validation.
