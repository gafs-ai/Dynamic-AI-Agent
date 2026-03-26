## Nuitka Build Rules

This document defines **project-wide** conventions for compiling Python components with **Nuitka**
as extension modules (`.pyd` on Windows, `.so` on Linux/macOS) and for testing the compiled output.

### Goals

- **Build outputs are reproducible** and can coexist for multiple CPU architectures.
- **Only the target component is resolved from the compiled artifact**, while the rest of the
  project remains importable from source.
- **Testing reuses existing pytest suites** (do not rewrite tests just to support compiled modules).

---

## 1. Build output layout

- **Base directory**: `Python/build/`
- **Architecture subdirectory**: `Python/build/<arch>/`

Recommended `<arch>` names:

- **Windows x64 (AMD64)**: `win_x64`
- **Windows ARM64**: `win_arm64`
- **Linux x64 (x86_64)**: `linux_x64`
- **Linux ARM64 (aarch64)**: `linux_arm64`
- **macOS x64 (x86_64)**: `darwin_x64`
- **macOS ARM64 (arm64)**: `darwin_arm64`

Each component’s Nuitka script should compile to `build/<arch>/` and then copy the resulting
`.pyd/.so` into:

- `build/<arch>/gafs/dynamicaiagent/`

This keeps compiled artifacts grouped by architecture and by logical import location.

---

## 2. Import rule: do NOT shadow `gafs`

**Do not** add `build/<arch>` as a top-level entry to `PYTHONPATH` (or `sys.path`).

Reason:

- If `build/<arch>` contains `gafs/` (and especially `gafs/__init__.py`), it can **shadow** the
  real source package and break imports such as `gafs.dynamicaiagent.common`.

### Correct pattern (preferred)

The project’s default build unit is **component-level** (e.g. `common`, `modelcomponent`, `edgeaicomponent`, etc.).
However, `common` and `utils` may be split further (because `common` can become large,
and `utils` aggregates unrelated, reusable helpers).

To avoid shadowing the top-level `gafs` package while still using a compiled artifact, prefer the compiled artifact
**only for the target package namespace** by prepending the build-time package directory to that package’s `__path__`.

Examples:

#### (A) Compiled subcomponent under `utils` (e.g. `utils.databaseprovider`)

Prepend the build-time `utils/` directory to `gafs.dynamicaiagent.utils.__path__`:

```python
from gafs.dynamicaiagent import utils as utils_pkg

build_utils_dir = "Python/build/<arch>/gafs/dynamicaiagent/utils"
if build_utils_dir not in utils_pkg.__path__:
    utils_pkg.__path__.insert(0, build_utils_dir)
```

This makes `gafs.dynamicaiagent.utils.<subcomponent>` resolve from the compiled output while keeping
`gafs.dynamicaiagent.common` and other packages resolved from source.

#### (B) Compiled subcomponent under `common` (future possibility)

Prepend the build-time `common/` directory to `gafs.dynamicaiagent.common.__path__` (same idea as above).

#### (C) Compiled top-level component (e.g. `modelcomponent`, `edgeaicomponent`)

Prepend the build-time `gafs/dynamicaiagent/` directory to `gafs.dynamicaiagent.__path__` so that only the target
top-level component is resolved from the compiled output.

---

## 3. Testing compiled modules (pytest wrapper)

To test a compiled component, create a wrapper test module:

- `Python/gafs/dynamicaiagent/<component>/test/test_build_<component>.py`
  - For `utils` subcomponents: `Python/gafs/dynamicaiagent/utils/<subcomponent>/test/test_build_<subcomponent>.py`
  - For `common` subcomponents (if split in the future): `Python/gafs/dynamicaiagent/common/<subcomponent>/test/test_build_<subcomponent>.py`

Rules:

- **Do not create new test cases** in the wrapper.
- Reuse the existing test module(s) by importing them after adjusting the appropriate package `__path__`
  (section 2).
- If the existing tests depend on files located next to the source tests (e.g. JSON config),
  ensure the wrapper loads the **source** test module, not a copy from `build/`.

Recommended approach:

- Adjust the relevant package `__path__` (section 2).
- Import and re-export the existing tests (and fixtures) from the source module.

---

## 4. Platform constraints

Nuitka outputs are **platform-dependent**:

- OS-specific (Windows/Linux/macOS)
- CPU-architecture-specific (x64/ARM64)
- Python-ABI-specific (e.g. `cp312` for Python 3.12)

Build and run tests on the target combination(s).

