"""Run test_symmetric_crypto_util against the Nuitka-compiled symmetriccryptoutil.

This module does NOT define new test cases. It makes pytest run the existing tests
while resolving `gafs.dynamicaiagent.utils.symmetriccryptoutil` from build/<arch>.
"""
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


THIS_FILE = Path(__file__).resolve()
PYTHON_ROOT = THIS_FILE.parents[5]  # .../Python/...
BUILD_DIR = PYTHON_ROOT / "build" / _get_build_arch_dir()
BUILD_UTILS_DIR = BUILD_DIR / "gafs" / "dynamicaiagent" / "utils"

if not BUILD_UTILS_DIR.is_dir():
    pytest.skip(
        f"Compiled module layout not found: {BUILD_UTILS_DIR}. Run symmetriccryptoutil/build_nuitka.py first.",
        allow_module_level=True,
    )

# Only prefer build/<arch>/.../utils for the `utils` package search path.
from gafs.dynamicaiagent import utils as _utils_pkg  # noqa: E402

build_utils_str = str(BUILD_UTILS_DIR)
if build_utils_str not in list(getattr(_utils_pkg, "__path__", [])):
    _utils_pkg.__path__.insert(0, build_utils_str)

# Import and re-export the existing tests.
from gafs.dynamicaiagent.utils.symmetriccryptoutil.test.test_symmetric_crypto_util import *  # noqa: F401,F403,E402

