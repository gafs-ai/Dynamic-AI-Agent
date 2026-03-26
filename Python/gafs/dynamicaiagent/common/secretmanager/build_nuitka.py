"""Build secretmanager as an extension module (.pyd on Windows, .so on Linux) with Nuitka.

Run from the project Python/ directory:

    python gafs/dynamicaiagent/common/secretmanager/build_nuitka.py

Requires: `pip install nuitka` and a C compiler.

The compiled module is placed under:
    build/<arch>/gafs/dynamicaiagent/common/

See `Documents/CodingRules/NuitkaBuildRules.md` for project-wide conventions.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGE = "gafs.dynamicaiagent.common.secretmanager"
PACKAGE_DIR = "gafs/dynamicaiagent/common/secretmanager"
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
    # .../Python/gafs/dynamicaiagent/common/secretmanager/build_nuitka.py -> Python/
    python_root = Path(__file__).resolve().parents[4]
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
    candidates = list(out_dir.glob("secretmanager*.pyd")) + list(
        out_dir.glob("secretmanager*.so")
    )
    if not candidates:
        print("Error: could not find compiled module in", out_dir)
        return 1
    compiled_path = candidates[0]

    # Copy the compiled module under build/<arch>/gafs/dynamicaiagent/common/
    target_dir = out_dir / "gafs" / "dynamicaiagent" / "common"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_compiled = target_dir / compiled_path.name
    shutil.copy2(compiled_path, target_compiled)

    print(f"Built: {target_compiled}")
    print("To verify the compiled module with tests:")
    print(
        "  pytest gafs/dynamicaiagent/common/secretmanager/test/test_build_secret_manager.py -v"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
