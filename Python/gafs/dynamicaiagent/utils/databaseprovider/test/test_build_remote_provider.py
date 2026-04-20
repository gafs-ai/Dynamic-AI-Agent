"""Pytest wrapper that runs the SurrealDB *remote* provider test suite against
the compiled databaseprovider extension module (.pyd / .so).

This file adjusts ``gafs.dynamicaiagent.utils.__path__`` so that the
compiled module takes precedence over the source package, then pre-registers
the source test module in ``sys.modules`` (so ``__file__`` is resolved to the
source directory and config JSON files are found), and finally re-exports all
test classes and fixtures via star-import.

Usage (run from the Python/ directory):
    pytest gafs/dynamicaiagent/utils/databaseprovider/test/test_build_remote_provider.py -v
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

# parents[5] of this file (…/databaseprovider/test/test_build_remote_provider.py)
# gives the Python/ project root.
_PYTHON_ROOT = Path(__file__).resolve().parents[5]
_BUILD_UTILS_DIR = (
    _PYTHON_ROOT / "build" / _get_build_arch_dir() / "gafs" / "dynamicaiagent" / "utils"
)

if not _BUILD_UTILS_DIR.is_dir():
    pytest.skip(
        f"Compiled module layout not found: {_BUILD_UTILS_DIR}. "
        "Run gafs/dynamicaiagent/utils/databaseprovider/build_nuitka.py first.",
        allow_module_level=True,
    )

# ── Adjust the utils package __path__ ────────────────────────────────────────

from gafs.dynamicaiagent import utils as _utils_pkg  # noqa: E402

_build_utils_str = str(_BUILD_UTILS_DIR)
if _build_utils_str not in list(getattr(_utils_pkg, "__path__", [])):
    _utils_pkg.__path__.insert(0, _build_utils_str)

# ── Pre-load the source test module so __file__ resolves to the source tree ──

# When the compiled databaseprovider package is active, Python would resolve
# submodule __file__ to a path inside the build output, causing JSON config
# lookups to fail.  By loading the test module from its actual source path
# and caching it in sys.modules under the expected qualified name, the star-
# import below uses the pre-loaded entry (correct __file__) instead of
# re-importing through the compiled package.

_REMOTE_TEST_MODULE = (
    "gafs.dynamicaiagent.utils.databaseprovider.test.test_surrealdb_remote_provider"
)
_remote_source_path = (
    _PYTHON_ROOT
    / "gafs"
    / "dynamicaiagent"
    / "utils"
    / "databaseprovider"
    / "test"
    / "test_surrealdb_remote_provider.py"
)

if _REMOTE_TEST_MODULE not in sys.modules:
    _spec = importlib.util.spec_from_file_location(_REMOTE_TEST_MODULE, _remote_source_path)
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules[_REMOTE_TEST_MODULE] = _mod
    _spec.loader.exec_module(_mod)

# ── Re-export all tests and fixtures so pytest can collect them ───────────────

from gafs.dynamicaiagent.utils.databaseprovider.test.test_surrealdb_remote_provider import *  # noqa: F401, F403, E402
