"""Safe launcher for the loopback-only notebook review server."""

from __future__ import annotations

import socket
import threading
import webbrowser
from pathlib import Path

import uvicorn

from notebook_classifier.app import create_app

LOOPBACK_HOST = "127.0.0.1"


def available_port(requested: int) -> int:
    """Validate a port, choosing an ephemeral loopback port when zero."""

    if not 0 <= requested <= 65_535:
        raise ValueError("port must be between 0 and 65535")
    if requested:
        return requested
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((LOOPBACK_HOST, 0))
        return int(probe.getsockname()[1])


def run_review_server(
    repository: Path,
    manifest: Path,
    *,
    port: int = 0,
    open_browser: bool = True,
) -> None:
    """Start a single local review session without exposing a host option."""

    selected_port = available_port(port)
    app = create_app(repository, manifest)
    url = (
        f"http://{LOOPBACK_HOST}:{selected_port}/session"
        f"?token={app.state.session_token}"
    )
    review = app.state.review
    print(f"Repository: {review.repository_root}", flush=True)
    print(f"Revision: {review.snapshot.repository_commit}", flush=True)
    print(f"Review URL: {url}", flush=True)
    if open_browser:
        threading.Timer(0.4, webbrowser.open, args=(url,)).start()
    uvicorn.run(
        app,
        host=LOOPBACK_HOST,
        port=selected_port,
        access_log=False,
        log_level="warning",
    )
