"""FastAPI app factory with port finder and common middleware."""

import socket
import sys
from pathlib import Path

import jinja2
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware


def find_available_port(start: int = 8000, end: int = 8099) -> int:
    """Find the first available port in the given range."""
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available port in range {start}-{end}")


def create_app(
    title: str,
    app_dir: str | Path,
    description: str = "",
) -> tuple[FastAPI, Jinja2Templates]:
    """Create a FastAPI app with static files and Jinja2 templates.

    Returns (app, templates) tuple.
    """
    app_dir = Path(app_dir)
    shared_dir = Path(__file__).parent

    app = FastAPI(title=title, description=description)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files if directory exists
    static_dir = app_dir / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Shared static assets
    shared_static = shared_dir / "static"
    if shared_static.exists():
        app.mount(
            "/shared-static",
            StaticFiles(directory=str(shared_static)),
            name="shared-static",
        )

    # Templates: app-specific first, then shared (use ChoiceLoader for Python 3.14 compat)
    loader = jinja2.ChoiceLoader([
        jinja2.FileSystemLoader(str(app_dir / "templates")),
        jinja2.FileSystemLoader(str(shared_dir / "templates")),
    ])
    env = jinja2.Environment(loader=loader, autoescape=True, auto_reload=True, cache_size=0)
    templates = Jinja2Templates(env=env)

    return app, templates


def run_app(app: FastAPI, default_port: int = 8000) -> None:
    """Start uvicorn on an available port."""
    port = find_available_port(default_port)
    print(f"\n  {app.title}")
    print(f"  http://127.0.0.1:{port}\n")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
