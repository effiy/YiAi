# YiAi Architecture

## Overview

FastAPI-based AI service backend with REST API endpoints. Modular design with dynamic extension support.

## Tech Stack

| Category | Technology |
|----------|-----------|
| Web Framework | FastAPI |
| ASGI Server | Uvicorn |
| Data Validation | Pydantic v2 |
| Database | MongoDB + Motor (async) |
| AI | Ollama (local LLM) |
| RSS | feedparser + APScheduler |
| Storage | OSS (oss2) + local fallback |
| Config | Pydantic Settings + YAML |
| CLI | typer + rich |
| HTTP Client | aiohttp |

## Directory Structure

```
main.py              # Entry (compatibility wrapper)
src/
├── main.py          # FastAPI app factory + lifecycle
├── api/routes/      # API endpoints
├── core/            # Config, DB, logger, exceptions, middleware, observer/
├── models/          # Pydantic schemas + collections
├── services/        # Business logic (execution, rss, ai, storage, state, database)
└── cli/             # CLI tools
```

## Key Architecture Patterns

1. **Module Execution Engine** — `/execution` endpoint dynamically executes allowlisted module methods. Supports sync/async, generators, async generators, SSE streaming.

2. **Configuration System** — Pydantic Settings with YAML + env var override. Nested YAML keys flattened to snake_case.

3. **Database** — MongoDB singleton via Motor async driver. Access via `core.database.db`.

4. **Lifecycle Management** — FastAPI lifespan manages MongoDB connections and RSS scheduler start/stop.

5. **Dual Storage Strategy** — File upload supports OSS cloud + local static storage with auto fallback.

6. **State Store** — Structured state record CRUD with `StateStoreService`, `SkillRecorder`, and `SessionAdapter`. Access via `/state/records` API and CLI.

7. **Observer Reliability** — 5-component reliability monitoring:
   - ThrottleMiddleware (IP rate limiting)
   - TailSampler (slow/error request sampling)
   - SandboxMiddleware (FS/network sandbox)
   - LazyStartManager (lazy initialization)
   - ReentrancyGuard (re-entry protection)
   - Middleware stack: Auth → CORS → Throttle → Sampler

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/execution` | Execute module method |
| POST | `/upload` | File upload |
| POST | `/upload-image-to-oss` | Image upload to OSS |
| POST | `/read-file` | Read file content |
| POST | `/write-file` | Write file |
| POST | `/delete-file` | Delete file |
| POST | `/delete-folder` | Delete folder |
| POST | `/rename-file` | Rename file |
| POST | `/rename-folder` | Rename folder |
| POST | `/wework/send-message` | WeChat Work message |
| POST | `/cleanup-unused-images` | Cleanup unused images |
| POST | `/state/records` | Create state record |
| GET | `/state/records` | Query state records |
| GET | `/state/records/{key}` | Get single record |
| PUT | `/state/records/{key}` | Update record |
| DELETE | `/state/records/{key}` | Delete record |
| GET | `/health/observer` | Observer health check |

## Database Collections

- `sessions` — user sessions
- `rss` — RSS articles
- `chat_records` — chat history
- `oss_file_info` — file metadata
- `oss_file_tags` — file tags
- `pet_data_sync` — pet data sync (optional)
- `seeds` — seed data (optional)
- `state_records` — structured state records
