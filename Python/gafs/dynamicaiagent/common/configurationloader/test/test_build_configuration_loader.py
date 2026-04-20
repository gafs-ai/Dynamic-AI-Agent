"""Run test_configuration_loader against the Nuitka-compiled configurationloader module.

This module does NOT define new test cases.  It makes pytest run the existing
tests while resolving ``gafs.dynamicaiagent.common.configurationloader`` from
the compiled ``build/<arch>/`` output.

Prerequisites:
    Run ``build_nuitka.py`` first to compile the module:
        python gafs/dynamicaiagent/common/configurationloader/build_nuitka.py
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
# This file is at:
#   Python/gafs/dynamicaiagent/common/configurationloader/test/test_build_configuration_loader.py
# parents[5] gives: Python/
THIS_FILE = Path(__file__).resolve()
PYTHON_ROOT = THIS_FILE.parents[5]
BUILD_DIR = PYTHON_ROOT / "build" / _get_build_arch_dir()
BUILD_COMMON_DIR = BUILD_DIR / "gafs" / "dynamicaiagent" / "common"

# Skip the entire module if the compiled output does not exist.
if not BUILD_COMMON_DIR.is_dir():
    pytest.skip(
        f"Compiled module layout not found: {BUILD_COMMON_DIR}. "
        "Run gafs/dynamicaiagent/common/configurationloader/build_nuitka.py first.",
        allow_module_level=True,
    )

# Adjust the common package __path__ so that Python resolves
# gafs.dynamicaiagent.common.configurationloader from the compiled build output
# instead of the source directory.  This avoids shadowing the top-level
# gafs package (see NuitkaBuildRules.md, Section 2, pattern B).
from gafs.dynamicaiagent import common as _common_pkg  # noqa: E402

build_common_str = str(BUILD_COMMON_DIR)
if build_common_str not in list(getattr(_common_pkg, "__path__", [])):
    _common_pkg.__path__.insert(0, build_common_str)

# Re-export all tests from the source test module so pytest collects them.
from gafs.dynamicaiagent.common.configurationloader.test.test_configuration_loader import *  # noqa: F401, F403, E402
