"""
Pytest configuration for cloudaicomponent tests.

Configures file logging so all test logs are recorded to test_run.log in this directory.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pytest


LOG_FILE = Path(__file__).resolve().parent / "test_run.log"
_FILE_HANDLER: logging.FileHandler | None = None
_ORIGINAL_ROOT_LEVEL: int | None = None


def pytest_configure(config: pytest.Config) -> None:
    """Add file handler to record all test logs to test_run.log."""
    global _FILE_HANDLER, _ORIGINAL_ROOT_LEVEL
    if _FILE_HANDLER is not None:
        return
    _ORIGINAL_ROOT_LEVEL = logging.root.level
    logging.root.setLevel(logging.DEBUG)
    _FILE_HANDLER = logging.FileHandler(LOG_FILE, encoding="utf-8")
    _FILE_HANDLER.setLevel(logging.DEBUG)
    _FILE_HANDLER.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    logging.root.addHandler(_FILE_HANDLER)


def pytest_unconfigure(config: pytest.Config) -> None:
    """Remove file handler and restore root logger level on teardown."""
    global _FILE_HANDLER, _ORIGINAL_ROOT_LEVEL
    if _FILE_HANDLER is not None:
        logging.root.removeHandler(_FILE_HANDLER)
        _FILE_HANDLER.close()
        _FILE_HANDLER = None
    if _ORIGINAL_ROOT_LEVEL is not None:
        logging.root.setLevel(_ORIGINAL_ROOT_LEVEL)
        _ORIGINAL_ROOT_LEVEL = None
