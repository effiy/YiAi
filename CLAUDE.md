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
| `python -m pytest tests/ -v` | Run all tests (if tests exist) |

## Architecture

### High-Level Structure

```
main.py (FastAPI entry, compatibility wrapper)
├── src/
│   ├── main.py (FastAPI application factory & lifecycle)
│   ├── api/routes/          # API endpoints
│   │   ├── execution.py     # Dynamic module execution
│   │   ├── upload.py        # File upload
│   │   ├── wework.py        # WeWork integration
│   │   └── maintenance.py   # Maintenance endpoints
│   ├── core/                 # Core infrastructure
│   │   ├── config.py        # Config (YAML + env vars)
│   │   ├── database.py      # MongoDB singleton
│   │   ├── logger.py        # Logging setup
│   │   ├── exceptions.py    # Custom exceptions
│   │   ├── response.py      # Unified response format
│   │   ├── middleware.py    # Authentication middleware
│   │   └── exception_handler.py # Exception handlers
│   ├── models/               # Pydantic models & collections
│   └── services/             # Business logic
│       ├── execution/       # Module executor
│       ├── rss/             # RSS feed management
│       ├── ai/              # Ollama chat service
│       ├── storage/         # OSS storage
│       ├── static/          # Static file service
│       └── database/        # Data access
├── config.yaml             # Configuration file
└── tests/                  # Tests directory (if exists)
```

### Key Architectural Patterns

1. **Module Execution Engine**: `/execution` endpoint allows dynamic execution of any whitelisted module method via GET/POST. Supports sync/async functions, generators, async generators, and SSE streaming.

2. **Configuration System**: Uses Pydantic Settings with YAML config file (`config.yaml`) + environment variable override. Nested YAML keys are flattened to snake_case (e.g., `server.host` → `server_host`).

3. **Database**: MongoDB singleton via Motor async driver. Access via `core.database.db` global instance.

4. **Lifecycle Management**: FastAPI lifespan manages MongoDB connection and RSS scheduler startup/shutdown in `src/main.py`.

## Configuration

- Primary config: `config.yaml`
- Environment variables override YAML config (uppercase, snake_case)
- Access via `core.config.settings` singleton

**Important Configs**:
- `module.allowlist`: Module execution whitelist (use `["*"]` for all)
- `mongodb.url`: MongoDB connection string
- `static.base_dir`: Static file directory
- `rss.scheduler_interval`: RSS poll interval in seconds
- `middleware.auth_enabled`: Enable/disable token authentication

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

## Module Execution (`services.execution.executor`)

The execution engine is the core of YiAi's extensibility:

- Whitelist controlled via `config.yaml` > `module.allowlist`
- Supports async/sync functions, generators, async generators
- Auto-detects function type and handles appropriately
- Parameters can be dict or JSON string
- SSE streaming for generator functions

**Example**:
```python
await execute_module(
    module_path="module.path",
    function_name="function_name",
    parameters={"key": "value"}
)
```

## Entry Points

- **Root `main.py`**: Compatibility wrapper that adds `src/` to path and imports from `src.main`
- **`src/main.py`**: Actual FastAPI application with `create_app()` factory and default `app` instance
- **Both files** can be used interchangeably to run the server
