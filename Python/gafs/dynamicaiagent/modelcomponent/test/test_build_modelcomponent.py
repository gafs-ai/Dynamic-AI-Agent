"""Run modelcomponent integration tests against the Nuitka-compiled modelcomponent.

This module does NOT define new test cases. Instead, it:

- Adjusts `gafs.dynamicaiagent.__path__` so that the compiled `modelcomponent` in build/<arch>/ is used.
- Then loads and re-exports the existing integration test modules from the source tree.

Usage:
    # From project Python/ directory, after running build_nuitka.py
    py -m pytest gafs/dynamicaiagent/modelcomponent/test/test_build_modelcomponent.py -v
"""

from __future__ import annotations

import importlib.util
import platform
import sys
from pathlib import Path

import pytest


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


THIS_FILE = Path(__file__).resolve()
PYTHON_ROOT = THIS_FILE.parents[4]  # .../Python/...

BUILD_BASE = "build"
ARCH_DIR = _get_build_arch_dir()
BUILD_DIR = PYTHON_ROOT / BUILD_BASE / ARCH_DIR
BUILD_DYNAMICAIAGENT_DIR = BUILD_DIR / "gafs" / "dynamicaiagent"

if not BUILD_DIR.is_dir():
    pytest.skip(
        f"Compiled module not found: {BUILD_DIR}. Run build_nuitka.py first for this architecture.",
        allow_module_level=True,
    )

if not BUILD_DYNAMICAIAGENT_DIR.is_dir():
    pytest.skip(
        f"Compiled module layout not found: {BUILD_DYNAMICAIAGENT_DIR}. Run build_nuitka.py first.",
        allow_module_level=True,
    )

# NOTE:
# Do NOT prepend build/<arch> to sys.path. That would shadow the top-level `gafs` package.
# Instead, prepend build/<arch>/gafs/dynamicaiagent to gafs.dynamicaiagent.__path__ so that
# only the compiled top-level component is resolved from the build output.
from gafs import dynamicaiagent as _dynamicaiagent_pkg  # noqa: E402

dyn_path = list(getattr(_dynamicaiagent_pkg, "__path__", []))
build_dyn_str = str(BUILD_DYNAMICAIAGENT_DIR)
if build_dyn_str not in dyn_path:
    _dynamicaiagent_pkg.__path__.insert(0, build_dyn_str)


def _load_source_test_module(source_path: Path, module_name: str) -> None:
    if not source_path.is_file():
        pytest.skip(
            f"Source test module not found: {source_path}",
            allow_module_level=True,
        )
    spec = importlib.util.spec_from_file_location(module_name, str(source_path))
    if spec is None or spec.loader is None:
        pytest.skip(
            f"Failed to create import spec for source test module: {source_path}",
            allow_module_level=True,
        )
    mod = importlib.util.module_from_spec(spec)
    # dataclasses (and some libraries) expect the module to exist in sys.modules
    # while executing class decorators.
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    for name, value in vars(mod).items():
        if name.startswith("_"):
            continue
        globals()[name] = value


SOURCE_TEST_DIR = (
    PYTHON_ROOT / "gafs" / "dynamicaiagent" / "modelcomponent" / "test"
)

_load_source_test_module(
    SOURCE_TEST_DIR / "conftest.py",
    "gafs.dynamicaiagent.modelcomponent.test.conftest",
)
_load_source_test_module(
    SOURCE_TEST_DIR / "test_model_catalogue_service.py",
    "gafs.dynamicaiagent.modelcomponent.test.test_model_catalogue_service",
)
_load_source_test_module(
    SOURCE_TEST_DIR / "test_model_service.py",
    "gafs.dynamicaiagent.modelcomponent.test.test_model_service",
)
_load_source_test_module(
    SOURCE_TEST_DIR / "test_model_component.py",
    "gafs.dynamicaiagent.modelcomponent.test.test_model_component",
)
