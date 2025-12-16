# PyMesh Fork - Patches and Changes

This is a fork of [PyMesh/PyMesh](https://github.com/PyMesh/PyMesh) maintained for building distributable Python wheels.

## Why This Fork Exists

The upstream PyMesh repository has not been updated since 2020 and uses outdated dependencies that don't compile with modern toolchains. This fork applies minimal patches to enable:

- Building with modern compilers (GCC 10+, Clang 15+, MSVC 2022)
- Support for Python 3.10, 3.11, and 3.12
- Cross-platform wheel builds (Linux, macOS ARM64, Windows)

## Summary of Changes

| Category | Change | Reason |
|----------|--------|--------|
| pybind11 | v2.4.3 → v2.11.1 | Python 3.11+ compatibility |
| Eigen | 2018 → 3.4.0 | Fix compiler bugs, better support |
| Cork | Vendored | Apply Windows compatibility fixes |
| Build | Add `-fcommon` | GCC 10+ compatibility |
| Build | Add `DYLD_LIBRARY_PATH` | macOS delocate finds third_party libs |
| Build | Use Ninja + parallel | Faster CI builds |
| Build | TBB static (not shared) | Avoid delocate dependency issues |
| Build | TBB cache marker fix | Check for library file, not just header |
| Build | Windows shebang fix | Use sys.executable for portability |
| Cork | Fallback M_PI define | MinGW ignores _USE_MATH_DEFINES |
| Python | Remove Tester | numpy 1.25+ compatibility |

## Detailed Changes

### 1. Dependency Updates

#### pybind11 (v2.4.3 → v2.11.1)
- **File**: `.gitmodules`
- **Change**: Point to official `github.com/pybind/pybind11` at v2.11.1
- **Reason**: pybind11 v2.4.3 is incompatible with Python 3.11+ due to `PyFrameObject` becoming opaque in Python 3.11

#### Eigen (2018 commit → 3.4.0)
- **File**: `.gitmodules`
- **Change**: Point to official `gitlab.com/libeigen/eigen` at tag 3.4.0
- **Reason**: The 2018 version had a bug in `Transpositions.h` (`trt.derived()` issue) and other compiler compatibility problems

### 2. Cork Library (Vendored)

Cork is now vendored directly instead of being a git submodule. This allows applying Windows compatibility fixes:

#### `third_party/cork/src/math/vec.h`
```cpp
// Added at top:
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#endif
```
**Reason**: Windows `<windows.h>` defines `min`/`max` macros that conflict with `std::min`/`std::max`

#### `third_party/cork/src/util/prelude.h`
```cpp
// Added before #include <cmath>:
#ifndef _USE_MATH_DEFINES
#define _USE_MATH_DEFINES
#endif
#include <math.h>
```
**Reason**: MSVC requires `_USE_MATH_DEFINES` to expose `M_PI` and other math constants

#### `third_party/cork/src/isct/fixint.h`
```cpp
// Changed from:
#ifdef _WIN32
#include <mpir.h>
#else
#include <gmp.h>
#endif

// To:
#include <gmp.h>
```
**Reason**: MPIR (a Windows fork of GMP) is no longer maintained (last release 2017). vcpkg provides GMP directly.

#### `third_party/cork/src/isct/gmpext4.h`
```cpp
// Changed from mpirxx.h to gmpxx.h on Windows
#include <gmpxx.h>
```
**Reason**: Same as above - use GMP instead of dead MPIR

### 3. Build System Fixes

#### `third_party/build.py` and `setup.py`
- **Change**: Add `-DCMAKE_POLICY_VERSION_MINIMUM=3.5`
- **Reason**: Modern CMake (3.27+) requires explicit minimum policy version for old CMakeLists.txt files

#### `third_party/build.py` - Cache Markers
- **Change**: TBB cache marker changed from `include/tbb/tbb.h` to `lib/libtbb.a`
- **Reason**: Previous marker only checked for headers, causing false cache hits when TBB library build failed but headers were installed

#### `setup.py` - Windows Compatibility
- **Change**: Use `sys.executable` to call `third_party/build.py` instead of relying on shebang
- **Reason**: Windows doesn't recognize Unix shebangs (`#!/usr/bin/env python`), causing WinError 193

#### CI Workflow (`.github/workflows/build-wheels.yml`)
- **Change**: Add `CFLAGS=-fcommon CXXFLAGS=-fcommon`
- **Reason**: GCC 10+ changed default from `-fcommon` to `-fno-common`, causing "multiple definition" linker errors in mmg and other C code with tentative definitions

### 4. Python Code Fixes

#### `python/pymesh/__init__.py`
- **Change**: Remove `from numpy.testing import Tester` and `test = Tester().test`
- **Reason**: `numpy.testing.Tester` was deprecated and removed in numpy 1.25

## Building Wheels

### Prerequisites

**Linux (Ubuntu/Debian)**:
```bash
sudo apt install cmake ninja-build libgmp-dev libmpfr-dev libboost-all-dev libeigen3-dev libcgal-dev swig
```

**macOS**:
```bash
brew install cmake ninja boost eigen cgal gmp mpfr swig
```

**Windows**:
```cmd
vcpkg install cgal:x64-windows boost-thread:x64-windows eigen3:x64-windows gmp:x64-windows mpfr:x64-windows
```

### Build

```bash
pip install build cibuildwheel
python -m build --wheel
```

## Releasing to PyPI

This fork uses GitHub Actions with [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/).

### One-Time Setup

1. Create/claim the `pymesh2` project on PyPI
2. Go to https://pypi.org/manage/project/pymesh2/settings/publishing/
3. Add a "trusted publisher":
   - Owner: `PozzettiAndrea`
   - Repository: `PyMesh`
   - Workflow: `build-wheels.yml`
   - Environment: (leave blank)

### Creating a Release

```bash
# 1. Update version in setup.py
# 2. Commit the version bump
git add setup.py
git commit -m "Bump version to 0.3.1"

# 3. Tag and push
git tag v0.3.1
git push origin main --tags
```

The CI will automatically:
1. Build wheels for Linux, macOS, Windows (Python 3.10-3.12)
2. Build source distribution
3. Run tests
4. Create GitHub release with wheels attached
5. Publish to PyPI

### Version Scheme

- `0.3.x` - Based on upstream PyMesh 0.3 with patches
- Increment patch version for each release with fixes

## Upstream Compatibility

This fork tracks upstream PyMesh. When upstream is updated, patches should be rebased or re-evaluated.

## License

Same as upstream PyMesh (MPL-2.0).
