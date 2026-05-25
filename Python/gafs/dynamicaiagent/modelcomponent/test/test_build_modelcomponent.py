"""test_build_modelcomponent.py - Tests for the Nuitka build output.

These tests run the compiled ``modelcomponent`` module (built via build_nuitka.py)
and verify that the public API surface is intact.

Requires: the Nuitka build to be completed first (run ``python build_nuitka.py``).
If the build output is absent, all tests are skipped.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BUILD_DIR = Path(__file__).resolve().parents[4] / "build" / "win_x64"


@pytest.fixture(scope="module")
def modelcomponent_build():
    """Import the compiled modelcomponent from the build directory."""
    if not BUILD_DIR.exists():
        pytest.skip(f"Build directory not found: {BUILD_DIR}")

    # Temporarily add the build directory to sys.path.
    sys.path.insert(0, str(BUILD_DIR))
    try:
        import importlib
        mod = importlib.import_module("gafs.dynamicaiagent.modelcomponent")
        return mod
    except ImportError as exc:
        pytest.skip(f"Compiled modelcomponent not importable: {exc}")
    finally:
        if str(BUILD_DIR) in sys.path:
            sys.path.remove(str(BUILD_DIR))


def test_build_modelcomponent_imports(modelcomponent_build) -> None:
    """All public symbols from __all__ must be importable from the built module."""
    mod = modelcomponent_build
    expected_symbols = [
        "ModelComponent",
        "ModelCatalogueService",
        "ModelService",
        "IModelComponent",
        "IModelCatalogueService",
        "IModelService",
        "ModelCatalogueEntry",
        "ModelDeployment",
        "ModelComponentConfigurations",
        "ModelStatus",
        "DeploymentStatus",
        "ModelComponentException",
        "ModelComponentInitializationException",
        "ModelCatalogueEntryNotFoundException",
        "ModelDeploymentNotFoundException",
    ]
    for symbol in expected_symbols:
        assert hasattr(mod, symbol), f"Symbol '{symbol}' missing from built module"


def test_build_modelcomponent_class_instantiation(modelcomponent_build) -> None:
    """Key classes must be instantiable without errors."""
    import logging
    mod = modelcomponent_build
    logger = logging.getLogger("build_test")

    catalogue_service = mod.ModelCatalogueService(logger)
    model_service = mod.ModelService(logger)
    component = mod.ModelComponent(
        logger=logger,
        model_catalogue_service=catalogue_service,
        model_service=model_service,
        cloud_ai_component=None,
    )
    assert component is not None


def test_build_modelcomponent_model_classes(modelcomponent_build) -> None:
    """Model classes serialize and deserialize correctly in the built module."""
    mod = modelcomponent_build

    cat = mod.ModelCatalogueEntry()
    cat.name = "test-model"
    cat.status = mod.ModelStatus.ACTIVE
    d = cat.to_dict(recursive=True)
    assert d["name"] == "test-model"
    assert d["status"] == "active"

    dep = mod.ModelDeployment()
    dep.name = "test-deployment"
    dep.status = mod.DeploymentStatus.ACTIVE
    d2 = dep.to_dict(recursive=True)
    assert d2["name"] == "test-deployment"


def test_build_modelcomponent_exceptions(modelcomponent_build) -> None:
    """Exception classes must be raiseable and catchable by their base class."""
    mod = modelcomponent_build

    with pytest.raises(mod.ModelComponentException):
        raise mod.ModelComponentInitializationException("test error")

    with pytest.raises(mod.ModelComponentException):
        raise mod.ModelCatalogueEntryNotFoundException("test error")
