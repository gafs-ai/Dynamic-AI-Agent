"""Pytest wrapper that runs the DatabaseManager test suite against the
compiled databasemanager extension module (.pyd / .so).

This file adjusts ``gafs.dynamicaiagent.common.__path__`` so that the
compiled module takes precedence over the source package, then pre-registers
the source test module in ``sys.modules`` (so ``__file__`` resolves to the
source directory), and finally re-exports all test classes and fixtures via
star-import.

Usage (run from the Python/ directory):
    pytest gafs/dynamicaiagent/common/databasemanager/test/test_build_database_manager.py -v

The compiled module must be built first:
    python gafs/dynamicaiagent/common/databasemanager/build_nuitka.py
"""
from __future__ import annotations

import importlib.util
import platform
import sys
from pathlib import Path

import pytest


def _get_build_arch_dir() -> str:
    plat = sys.platform
    machine = platform.machine().upper()
    if plat == "win32":
        return "win_x64" if machine == "AMD64" else "win_arm64"
    if plat == "linux":
        return "linux_x64" if machine == "X86_64" else "linux_arm64"
    if plat == "darwin":
        return "darwin_x64" if machine == "X86_64" else "darwin_arm64"
    return f"{plat}_{machine.lower()}"


# ── Path resolution ───────────────────────────────────────────────────────────

# parents[5] of this file (…/common/databasemanager/test/test_build_database_manager.py)
# → Python/ project root.
_PYTHON_ROOT = Path(__file__).resolve().parents[5]
_BUILD_COMMON_DIR = (
    _PYTHON_ROOT / "build" / _get_build_arch_dir() / "gafs" / "dynamicaiagent" / "common"
)

if not _BUILD_COMMON_DIR.is_dir():
    pytest.skip(
        f"Compiled module layout not found: {_BUILD_COMMON_DIR}. "
        "Run gafs/dynamicaiagent/common/databasemanager/build_nuitka.py first.",
        allow_module_level=True,
    )

# ── Adjust the common package __path__ ───────────────────────────────────────

from gafs.dynamicaiagent import common as _common_pkg  # noqa: E402

_build_common_str = str(_BUILD_COMMON_DIR)
if _build_common_str not in list(getattr(_common_pkg, "__path__", [])):
    _common_pkg.__path__.insert(0, _build_common_str)

# ── Pre-load the source test module so __file__ resolves to the source tree ──

_TEST_MODULE_NAME = "gafs.dynamicaiagent.common.databasemanager.test.test_database_manager"
_source_test_path = (
    _PYTHON_ROOT
    / "gafs"
    / "dynamicaiagent"
    / "common"
    / "databasemanager"
    / "test"
    / "test_database_manager.py"
)

if _TEST_MODULE_NAME not in sys.modules:
    _spec = importlib.util.spec_from_file_location(_TEST_MODULE_NAME, _source_test_path)
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules[_TEST_MODULE_NAME] = _mod
    _spec.loader.exec_module(_mod)

# ── Re-export all tests and fixtures so pytest can collect them ───────────────

from gafs.dynamicaiagent.common.databasemanager.test.test_database_manager import *  # noqa: F401, F403, E402

