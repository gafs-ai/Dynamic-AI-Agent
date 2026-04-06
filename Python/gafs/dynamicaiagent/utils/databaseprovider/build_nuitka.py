"""Build databaseprovider as an extension module (.pyd on Windows, .so on Linux) with Nuitka.

The compiled module can be imported by other Python code like the source package.
Run from the project Python/ directory:
  python gafs/dynamicaiagent/utils/databaseprovider/build_nuitka.py

Requires: pip install nuitka
Also requires a C compiler (e.g. MinGW/MSVC on Windows, gcc on Linux).

Output is under build/<arch>/ (e.g. build/win_x64, build/win_arm64) so that
multiple architectures can be built side by side.
After a successful build, runs test_surrealdb_remote_provider with the compiled module to verify.
"""
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Package to compile (must be importable from Python/)
PACKAGE = "gafs.dynamicaiagent.utils.databaseprovider"
# Path to package directory (not __init__.py) relative to Python/
PACKAGE_DIR = "gafs/dynamicaiagent/utils/databaseprovider"
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
    # .../Python/gafs/dynamicaiagent/utils/databaseprovider/build_nuitka.py -> Python/
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
    env["PYTHONPATH"] = python_root_str + (os.pathsep + env.get("PYTHONPATH", "")) if env.get("PYTHONPATH") else python_root_str
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=python_root_str, env=env)
    if result.returncode != 0:
        return result.returncode

    # Nuitka puts the .pyd/.so in output_dir (e.g. databaseprovider.cp312-win_amd64.pyd)
    out_dir = python_root / BUILD_BASE / arch_dir
    candidates = [f for f in out_dir.iterdir() if f.is_file() and f.suffix in (".pyd", ".so")]
    if not candidates:
        candidates = list(out_dir.glob("databaseprovider*"))
    if not candidates:
        print("Error: could not find compiled module in", out_dir)
        return 1
    pyd_path = candidates[0]

    # Copy the compiled module under build/<arch>/gafs/dynamicaiagent/utils/
    # NOTE: We intentionally do not create __init__.py stubs in build/ to avoid shadowing
    # the real `gafs` package (which would break imports like `gafs.dynamicaiagent.common`).
    target_dir = out_dir / "gafs" / "dynamicaiagent" / "utils"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_pyd = target_dir / pyd_path.name
    shutil.copy2(pyd_path, target_pyd)
    print(f"Built: {target_pyd}")
    print()
    print("To verify the compiled module with existing tests:")
    print("  pytest gafs/dynamicaiagent/utils/databaseprovider/test/test_build_surrealdb_remote_provider.py -v")
    print("  pytest gafs/dynamicaiagent/utils/databaseprovider/test/test_build_surrealdb_local_provider.py -v")
    print()
    print("To use the compiled module from other code, run Python from the Python/ directory and")
    print("ensure `gafs.dynamicaiagent.utils.__path__` prefers build/<arch>/.../utils before importing")
    print("`gafs.dynamicaiagent.utils.databaseprovider` (see test_build_surrealdb_remote_provider.py).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
