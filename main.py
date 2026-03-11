#!/usr/bin/env python3
"""YiAi API Server - Root Entry Point.

For production use, consider: `uvicorn main:app --host 0.0.0.0 --port 8000`
"""
import sys
import os

# Disable __pycache__ generation
sys.dont_write_bytecode = True

# Add the project root to path to support the src layout
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import app, create_app

if __name__ == "__main__":
    import uvicorn
    from core.config import settings

    host = settings.server_host
    port = settings.server_port
    reload = settings.server_reload

    print(f"Starting server: http://{host}:{port}")
    print(f"Auto-reload: {'Enabled' if reload else 'Disabled'}")

    log_level = settings.logging_level.lower()
    limit_concurrency = settings.uvicorn_limit_concurrency
    limit_max_requests = settings.uvicorn_limit_max_requests
    timeout_keep_alive = settings.uvicorn_timeout_keep_alive

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        limit_concurrency=limit_concurrency,
        limit_max_requests=limit_max_requests,
        timeout_keep_alive=timeout_keep_alive
    )
