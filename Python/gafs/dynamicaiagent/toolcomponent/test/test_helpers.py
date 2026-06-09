"""test_helpers.py - Shared utility functions for toolcomponent integration tests."""

from __future__ import annotations

import time


def unique_suffix() -> str:
    """Return a millisecond timestamp string usable as a unique record name suffix."""
    return str(int(time.time() * 1000))


def is_docker_available() -> bool:
    """Return True if the Docker daemon is reachable via the SDK."""
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False
