"""Run cloudaicomponent tests against the Nuitka-compiled Cloud AI Component.

This module does NOT define new test cases. It adjusts the import path so that
`gafs.dynamicaiagent.cloudaicomponent` is imported from the compiled artifact
under `build/<arch>/gafs/dynamicaiagent/cloudaicomponent`, and then re-exports
the existing tests from the source test modules.

Usage:
    1. From the `Python/` directory, build with:
           python gafs/dynamicaiagent/cloudaicomponent/build_nuitka.py
    2. Then run:
           pytest gafs/dynamicaiagent/cloudaicomponent/test/test_build_cloudaicomponent.py -v
"""

from __future__ import annotations

import platform
import sys
from pathlib import Path

import pytest


def _get_build_arch_dir() -> str:
    """Mirror the arch naming used by build_nuitka.py."""
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
# .../Python/gafs/dynamicaiagent/cloudaicomponent/test/test_build_cloudaicomponent.py -> .../Python
PYTHON_ROOT = THIS_FILE.parents[4]
BUILD_DIR = PYTHON_ROOT / "build" / _get_build_arch_dir()
BUILD_DYNAMICAIAGENT_DIR = BUILD_DIR / "gafs" / "dynamicaiagent"


if not BUILD_DYNAMICAIAGENT_DIR.is_dir():
    pytest.skip(
        f"Compiled cloudaicomponent layout not found: {BUILD_DYNAMICAIAGENT_DIR}. "
        f"Run cloudaicomponent/build_nuitka.py first.",
        allow_module_level=True,
    )


# Prefer build/<arch>/.../dynamicaiagent for the `dynamicaiagent` package search path.
from gafs import dynamicaiagent as _dyn_pkg  # noqa: E402


build_dyn_str = str(BUILD_DYNAMICAIAGENT_DIR)
if build_dyn_str not in list(getattr(_dyn_pkg, "__path__", [])):
    _dyn_pkg.__path__.insert(0, build_dyn_str)


# Import and re-export the existing tests so they run against the compiled package.
from gafs.dynamicaiagent.cloudaicomponent.test.test_azure_openai_provider_integration import *  # noqa: F401,F403,E402
from gafs.dynamicaiagent.cloudaicomponent.test.test_openai_provider_integration import *  # noqa: F401,F403,E402
from gafs.dynamicaiagent.cloudaicomponent.test.test_cloud_ai_component_integration import *  # noqa: F401,F403,E402

