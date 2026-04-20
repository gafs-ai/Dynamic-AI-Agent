"""Run test_crypto_util against the Nuitka-compiled cryptoutil module.

This module does NOT define new test cases. It makes pytest run the existing
tests while resolving ``gafs.dynamicaiagent.utils.cryptoutil`` from
``build/<arch>/``.

Prerequisites:
    Run ``build_nuitka.py`` first to compile the module:
        python gafs/dynamicaiagent/utils/cryptoutil/build_nuitka.py
"""
import platform
import sys
from pathlib import Path

import pytest


def _get_build_arch_dir() -> str:
    """Return the architecture-specific build subdirectory name."""
    plat = sys.platform
    machine = platform.machine().upper()

    if plat == "win32":
        return "win_x64" if machine == "AMD64" else "win_arm64"
    if plat == "linux":
        return "linux_x64" if machine == "X86_64" else "linux_arm64"
    if plat == "darwin":
        return "darwin_x64" if machine == "X86_64" else "darwin_arm64"

    return f"{plat}_{machine.lower()}"


# Resolve paths.
# This file is at: Python/gafs/dynamicaiagent/utils/cryptoutil/test/test_build_crypto_util.py
# parents[5] gives: Python/
THIS_FILE = Path(__file__).resolve()
PYTHON_ROOT = THIS_FILE.parents[5]
BUILD_DIR = PYTHON_ROOT / "build" / _get_build_arch_dir()
BUILD_UTILS_DIR = BUILD_DIR / "gafs" / "dynamicaiagent" / "utils"

# Skip the entire module if the compiled output does not exist.
if not BUILD_UTILS_DIR.is_dir():
    pytest.skip(
        f"Compiled module layout not found: {BUILD_UTILS_DIR}. "
        "Run gafs/dynamicaiagent/utils/cryptoutil/build_nuitka.py first.",
        allow_module_level=True,
    )

# Adjust the utils package __path__ so that Python resolves
# gafs.dynamicaiagent.utils.cryptoutil from the compiled build output
# instead of the source directory. This avoids shadowing the top-level
# gafs package (see NuitkaBuildRules.md, Section 2).
from gafs.dynamicaiagent import utils as _utils_pkg  # noqa: E402

build_utils_str = str(BUILD_UTILS_DIR)
if build_utils_str not in list(getattr(_utils_pkg, "__path__", [])):
    _utils_pkg.__path__.insert(0, build_utils_str)

# Re-export all tests from the source test module so pytest collects them.
from gafs.dynamicaiagent.utils.cryptoutil.test.test_crypto_util import *  # noqa: F401, F403, E402
