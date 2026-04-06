"""Pytest conftest: add Python source root to sys.path before collecting tests.

Ensures 'gafs' is importable when pytest runs from this directory or from parent.
Run integration tests from this directory (Python)::
  python -m pytest gafs/dynamicaiagent/modelcomponent/test/test_model_catalogue_service_integration.py -v
"""
from pathlib import Path
import sys

_root = Path(__file__).resolve().parent
_root_str = str(_root)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)


def _clear_callable_cause(exc):
    """Clear exception.__cause__ when it is callable (avoids pytest/traceback AttributeError)."""
    if exc is None:
        return
    cause = getattr(exc, "__cause__", None)
    if cause is not None and callable(cause):
        exc.__cause__ = None
    # Recursively clear in case __cause__ is an exception with a callable __cause__
    if cause is not None and isinstance(cause, BaseException):
        _clear_callable_cause(cause)


def pytest_runtest_makereport(item, call):
    """Before building the failure report, clear __cause__ when it is a callable.

    Some libraries (e.g. SurrealDB client) set exception.__cause__ to a non-exception,
    which makes traceback.format_exception_only raise AttributeError when accessing
    e.__cause__.__traceback__. Clearing __cause__ when callable lets pytest show the failure.
    """
    if call.excinfo is not None and call.excinfo.value is not None:
        _clear_callable_cause(call.excinfo.value)
    return None  # let other plugins build the report
