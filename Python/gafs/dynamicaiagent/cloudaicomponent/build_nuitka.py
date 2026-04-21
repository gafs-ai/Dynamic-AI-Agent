"""Build cloudaicomponent as an extension module (.pyd on Windows, .so on Linux) with Nuitka.

Run from the project Python/ directory:

    python gafs/dynamicaiagent/cloudaicomponent/build_nuitka.py

Requires: `pip install nuitka` and a C compiler.

The compiled module is placed under:
    build/<arch>/gafs/dynamicaiagent/cloudaicomponent/

See `Documents/CodingRules/NuitkaBuildRules.md` for project-wide conventions.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGE = "gafs.dynamicaiagent.cloudaicomponent"
PACKAGE_DIR = "gafs/dynamicaiagent/cloudaicomponent"
BUILD_BASE = "build"


def get_build_arch_dir() -> str:
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


def main() -> int:
    # .../Python/gafs/dynamicaiagent/cloudaicomponent/build_nuitka.py -> Python/
    python_root = Path(__file__).resolve().parents[3]
    python_root_str = str(python_root)

    arch_dir = get_build_arch_dir()
    output_dir = f"{BUILD_BASE}/{arch_dir}"

    package_path = python_root / PACKAGE_DIR.replace("/", os.sep)
    if not package_path.is_dir():
        print(f"Error: package directory not found: {package_path}")
        return 1

    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--module",
        "--output-dir=" + output_dir,
        "--include-package=" + PACKAGE,
        "--include-package-data=" + PACKAGE,
        "--assume-yes-for-downloads",
        str(package_path),
    ]

    # Nuitka needs PYTHONPATH to resolve imports from the package
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        python_root_str + (os.pathsep + env.get("PYTHONPATH", ""))
        if env.get("PYTHONPATH")
        else python_root_str
    )

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=python_root_str, env=env)
    if result.returncode != 0:
        return result.returncode

    out_dir = python_root / BUILD_BASE / arch_dir
    # Prefer matching cloudaicomponent.*.pyd/.so
    candidates = list(out_dir.glob("cloudaicomponent*.pyd")) + list(
        out_dir.glob("cloudaicomponent*.so")
    )
    if not candidates:
        # Fallback: any .pyd/.so in out_dir
        candidates = [f for f in out_dir.iterdir() if f.is_file() and f.suffix in (".pyd", ".so")]
    if not candidates:
        print("Error: could not find compiled module in", out_dir)
        return 1
    compiled_path = candidates[0]

    # Copy the compiled module under build/<arch>/gafs/dynamicaiagent/cloudaicomponent
    target_dir = out_dir / "gafs" / "dynamicaiagent" / "cloudaicomponent"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_compiled = target_dir / compiled_path.name
    shutil.copy2(compiled_path, target_compiled)

    print(f"Built: {target_compiled}")
    print("To verify the compiled module with tests:")
    print("  pytest gafs/dynamicaiagent/cloudaicomponent/test/test_build_cloudaicomponent.py -v")
    return 0


if __name__ == "__main__":
    sys.exit(main())
