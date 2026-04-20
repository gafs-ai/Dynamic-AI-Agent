"""Build configurationloader as an extension module (.pyd on Windows, .so on Linux) with Nuitka.

Output is placed under build/<arch>/ (e.g. build/win_x64) so that multiple
architectures can coexist side by side.

Usage (run from the Python/ directory):
    python gafs/dynamicaiagent/common/configurationloader/build_nuitka.py
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Fully qualified package name and its source path relative to Python/.
PACKAGE = "gafs.dynamicaiagent.common.configurationloader"
PACKAGE_DIR = "gafs/dynamicaiagent/common/configurationloader"

# Base directory for all build outputs (relative to Python/ root).
BUILD_BASE = "build"


def get_build_arch_dir() -> str:
    """Return the architecture-specific subdirectory name.

    Returns:
        A string such as ``"win_x64"``, ``"win_arm64"``, ``"linux_x64"``, etc.
    """
    plat = sys.platform
    machine = platform.machine().upper()

    if plat == "win32":
        return "win_x64" if machine == "AMD64" else "win_arm64"
    if plat == "linux":
        return "linux_x64" if machine == "X86_64" else "linux_arm64"
    if plat == "darwin":
        return "darwin_x64" if machine == "X86_64" else "darwin_arm64"

    # Fallback for other platforms.
    return f"{plat}_{machine.lower()}"


def main() -> int:
    """Run the Nuitka build and copy the compiled module to the output directory.

    Returns:
        Exit code (0 = success, non-zero = failure).
    """
    # Resolve the Python/ root directory from this script's location.
    # Path layout: Python/gafs/dynamicaiagent/common/configurationloader/build_nuitka.py
    #              parents[4] gives Python/
    python_root = Path(__file__).resolve().parents[4]
    python_root_str = str(python_root)

    # Determine the architecture-specific output subdirectory.
    arch_dir = get_build_arch_dir()
    output_dir = f"{BUILD_BASE}/{arch_dir}"

    # Verify that the package source directory exists before invoking Nuitka.
    package_path = python_root / PACKAGE_DIR.replace("/", os.sep)
    if not package_path.is_dir():
        print(f"Error: package directory not found: {package_path}")
        return 1

    # Build the Nuitka command.
    # --module:                   Compile as an importable extension module.
    # --output-dir:               Where to place the compiled output.
    # --include-package:          Bundle the entire package (including sub-packages).
    # --include-package-data:     Include non-Python data files inside the package.
    # --assume-yes-for-downloads: Non-interactive mode (auto-download C compiler if needed).
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

    # Nuitka needs PYTHONPATH to resolve local imports (gafs.*).
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        python_root_str + os.pathsep + existing_pythonpath
        if existing_pythonpath
        else python_root_str
    )

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=python_root_str, env=env)
    if result.returncode != 0:
        return result.returncode

    # Locate the compiled module in the output directory.
    out_dir = python_root / BUILD_BASE / arch_dir
    candidates = (
        list(out_dir.glob("configurationloader*.pyd"))
        + list(out_dir.glob("configurationloader*.so"))
    )
    if not candidates:
        print("Error: could not find compiled module in", out_dir)
        return 1
    compiled_path = candidates[0]

    # Copy the compiled module to build/<arch>/gafs/dynamicaiagent/common/
    # so that tests can load it by adjusting gafs.dynamicaiagent.common.__path__
    # (see NuitkaBuildRules.md, Section 2 – pattern B).
    target_dir = out_dir / "gafs" / "dynamicaiagent" / "common"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / compiled_path.name
    shutil.copy2(compiled_path, target_path)
    print(f"Compiled module copied to: {target_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
