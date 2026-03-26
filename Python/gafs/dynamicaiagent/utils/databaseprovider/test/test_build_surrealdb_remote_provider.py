"""Run test_surrealdb_remote_provider against the Nuitka-compiled databaseprovider.

This module does NOT define new test cases. Instead, it:
- Adjusts `gafs.dynamicaiagent.utils.__path__` so that the compiled module in build/<arch>/ is used.
- Then imports all tests from test_surrealdb_remote_provider.

Usage:
    # From project Python/ directory, after running build_nuitka.py
    pytest gafs/dynamicaiagent/utils/databaseprovider/test/test_build_surrealdb_remote_provider.py -v
"""
import platform
import sys
from pathlib import Path

import pytest

import importlib.util


def _get_build_arch_dir() -> str:
    """Return architecture-specific subdir name: win_x64, win_arm64, linux_x64, etc."""
    plat = sys.platform
    machine = platform.machine().upper()
    if plat == "win32":
        return "win_x64" if machine == "AMD64" else "win_arm64"
    if plat == "linux":
        return "linux_x64" if machine == "X86_64" else "linux_arm64"
    if plat == "darwin":
        return "darwin_x64" if machine == "X86_64" else "darwin_arm64"
    return f"{plat}_{machine.lower()}"


# Resolve project Python/ root
THIS_FILE = Path(__file__).resolve()
PYTHON_ROOT = THIS_FILE.parents[5]  # .../Python/...

BUILD_BASE = "build"
ARCH_DIR = _get_build_arch_dir()
BUILD_DIR = PYTHON_ROOT / BUILD_BASE / ARCH_DIR
BUILD_UTILS_DIR = BUILD_DIR / "gafs" / "dynamicaiagent" / "utils"


if not BUILD_DIR.is_dir():
    pytest.skip(
        f"Compiled module not found: {BUILD_DIR}. Run build_nuitka.py first for this architecture.",
        allow_module_level=True,
    )

if not BUILD_UTILS_DIR.is_dir():
    pytest.skip(
        f"Compiled module layout not found: {BUILD_UTILS_DIR}. Run build_nuitka.py first.",
        allow_module_level=True,
    )

# NOTE:
# Do NOT prepend build/<arch> to sys.path. That would shadow the top-level `gafs` package and
# break imports like `gafs.dynamicaiagent.common`. Instead, we only prepend build/<arch>/.../utils
# to the utils package search path, so that ONLY `databaseprovider` is resolved from the build.
from gafs.dynamicaiagent import utils as _utils_pkg  # noqa: E402

utils_path = list(getattr(_utils_pkg, "__path__", []))
build_utils_str = str(BUILD_UTILS_DIR)
if build_utils_str not in utils_path:
    _utils_pkg.__path__.insert(0, build_utils_str)

# Load the *source* test module from the workspace path, but with the compiled
# databaseprovider available on utils.__path__. This avoids importing the test
# module from the build output (which may not contain config files).
SOURCE_TEST_PATH = (
    PYTHON_ROOT
    / "gafs"
    / "dynamicaiagent"
    / "utils"
    / "databaseprovider"
    / "test"
    / "test_surrealdb_remote_provider.py"
)
if not SOURCE_TEST_PATH.is_file():
    pytest.skip(
        f"Source test module not found: {SOURCE_TEST_PATH}",
        allow_module_level=True,
    )

spec = importlib.util.spec_from_file_location(
    "gafs.dynamicaiagent.utils.databaseprovider.test._source_test_surrealdb_remote_provider",
    str(SOURCE_TEST_PATH),
)
if spec is None or spec.loader is None:
    pytest.skip(
        "Failed to create import spec for source test module.",
        allow_module_level=True,
    )
_source_tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_source_tests)  # type: ignore[union-attr]

# Re-export source module symbols so pytest can collect fixtures and tests
# from this wrapper module. (We keep dunder/private names out.)
for _name, _value in vars(_source_tests).items():
    if _name.startswith("_"):
        continue
    globals()[_name] = _value


