from __future__ import annotations

"""Wrapper tests for running DatabaseManager tests against the Nuitka-compiled module.

This module:
- Adjusts `gafs.dynamicaiagent.common.__path__` so that
  `gafs.dynamicaiagent.common.databasemanager` is imported from the compiled artifact
  under `build/<arch>/gafs/dynamicaiagent/common/`.
- Then loads the existing source test module
  `gafs.dynamicaiagent.common.databasemanager.test.test_database_manager`
  and re-exports all of its public symbols.

See `Documents/CodingRules/NuitkaBuildRules.md` for details.
"""

import importlib.util
import os
from pathlib import Path

import pytest

from gafs.dynamicaiagent import common as common_pkg


def _get_build_arch_dir() -> str:
    """Mirror the arch naming used by build_nuitka.py."""
    import platform
    import sys

    plat = sys.platform
    machine = platform.machine().upper()
    if plat == "win32":
        return "win_x64" if machine == "AMD64" else "win_arm64"
    if plat == "linux":
        return "linux_x64" if machine == "X86_64" else "linux_arm64"
    if plat == "darwin":
        return "darwin_x64" if machine == "X86_64" else "darwin_arm64"
    return f"{plat}_{machine.lower()}"


def _adjust_common_path_for_compiled() -> None:
    """Prepend build/<arch>/gafs/dynamicaiagent/common to common.__path__."""
    python_root = Path(__file__).resolve().parents[5]  # .../Python/
    arch_dir = _get_build_arch_dir()
    build_common_dir = (
        python_root
        / "build"
        / arch_dir
        / "gafs"
        / "dynamicaiagent"
        / "common"
    )
    if build_common_dir.is_dir():
        build_common_str = str(build_common_dir)
        if build_common_str not in common_pkg.__path__:
            common_pkg.__path__.insert(0, build_common_str)
    else:
        pytest.skip(f"Compiled databasemanager not found at {build_common_dir}")


_adjust_common_path_for_compiled()


def _load_source_tests():
    """Load the original pytest module from source and return it."""
    python_root = Path(__file__).resolve().parents[5]  # .../Python/
    source_test_path = (
        python_root
        / "gafs"
        / "dynamicaiagent"
        / "common"
        / "databasemanager"
        / "test"
        / "test_database_manager.py"
    )

    if not source_test_path.is_file():
        raise FileNotFoundError(f"Source test module not found: {source_test_path}")

    spec = importlib.util.spec_from_file_location(
        "gafs.dynamicaiagent.common.databasemanager.test.test_database_manager",
        source_test_path,
    )
    if spec is None or spec.loader is None:
        raise ImportError("Failed to create module spec for source tests.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_source_tests = _load_source_tests()

# Re-export all public attributes (tests, fixtures, etc.) from the source module.
for _name, _value in vars(_source_tests).items():
    if not _name.startswith("_"):
        globals()[_name] = _value

