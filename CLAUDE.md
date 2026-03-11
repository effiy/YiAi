# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YiAi is a FastAPI-based AI service backend providing RSS management, file upload, AI chat, and dynamic module execution capabilities via REST API endpoints.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start development server
python main.py
```

Server runs at http://localhost:8000 with auto-reload enabled. API docs available at /docs and /redoc.

## Key Commands

| Command | Purpose |
|---------|---------|
| `python main.py` | Start development server |
| `python scripts/rss_manager.py --list` | List RSS feeds |
| `python scripts/rss_manager.py --add <url>` | Add RSS feed |
| `python scripts/import_dir_to_sessions.py --dir <path>` | Import directory to sessions |

## Architecture

### High-Level Structure

```
main.py (FastAPI entry)
├── api/routes/          # API endpoints
│   ├── debug.py         # Debug/health endpoints
│   ├── execution.py     # Dynamic module execution
│   ├── upload.py        # File upload
│   └── wework.py        # WeWork integration
├── core/                 # Core infrastructure
│   ├── settings.py      # Config (YAML + env vars)
│   ├── database.py      # MongoDB singleton
│   ├── logger.py        # Logging setup
│   ├── exceptions.py    # Custom exceptions
│   ├── response.py      # Unified response format
│   └── schemas.py       # Pydantic models
└── services/             # Business logic
    ├── execution/       # Module executor
    ├── rss/             # RSS feed management
    ├── ai/              # Ollama chat service
    ├── storage/         # OSS storage
    ├── static/          # Static file service
    └── database/        # Data access
```

### Key Architectural Patterns

1. **Module Execution Engine**: `/execution` endpoint allows dynamic execution of any whitelisted module method via GET/POST. Supports sync/async functions and SSE streaming.

2. **Configuration System**: Uses Pydantic Settings with YAML config file (`config.yaml`) + environment variable override. Nested YAML keys are flattened to snake_case (e.g., `server.host` → `server_host`).

3. **Database**: MongoDB singleton via Motor async driver. Access via `core.database.db` instance.

4. **Lifecycle Management**: FastAPI lifespan manages MongoDB connection and RSS scheduler startup/shutdown.

## Important Modules

### Module Execution (`services.execution.executor`)

- Whitelist controlled via `config.yaml` > `module.allowlist`
- Supports async/sync functions, generators, async generators
- Auto-detects function type and handles appropriately
- Parameters can be dict or JSON string

**Example**:
```python
await execute_module(
    module_path="module.path",
    function_name="function_name",
    parameters={"key": "value"}
)
```

### RSS Service (`services.rss`)

- `rss_scheduler.py`: APScheduler-based polling
- `feed_service.py`: Feed parsing and storage
- Runs automatically on startup if `startup.init_rss_system = true`

## Configuration

- Primary config: `config.yaml`
- Environment variables override YAML config (uppercase, snake_case)
- Access via `core.settings.settings` singleton

**Important Configs**:
- `module.allowlist`: Module execution whitelist (use `["*"]` for all)
- `mongodb.url`: MongoDB connection string
- `static.base_dir`: Static file directory
- `rss.scheduler_interval`: RSS poll interval in seconds

## Database Collections

- `sessions`: User sessions
- `rss`: RSS articles
- `chat_records`: Chat history
- `oss_file_info`: File metadata
- `oss_file_tags`: File tags

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/execution` | Execute module method |
| POST | `/upload` | Upload files |
| GET | `/debug/info` | System info |
| GET | `/debug/health` | Health check |

## Data Flow Example: Module Execution

```
Request → api/routes/execution.py
         ↓
services/execution/executor.py (validate whitelist, import module)
         ↓
Target service function
         ↓
Response (JSON or SSE stream)
```
