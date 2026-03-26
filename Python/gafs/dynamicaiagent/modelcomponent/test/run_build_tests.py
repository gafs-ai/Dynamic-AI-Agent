"""Run modelcomponent integration tests against the Nuitka build artifact.

This is a thin script around pytest that targets the build-wrapper test module.

Usage (from Python/ directory, after building):
    py gafs/dynamicaiagent/modelcomponent/test/run_build_tests.py -v
"""

from __future__ import annotations

import sys

import pytest


def main(argv: list[str]) -> int:
    args = [
        "gafs/dynamicaiagent/modelcomponent/test/test_build_modelcomponent.py",
        *argv,
    ]
    return pytest.main(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
