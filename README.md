# PyMesh2

<div align="center">
<a href="https://pozzettiandrea.github.io/PyMesh/">
<img src="https://pozzettiandrea.github.io/PyMesh/preview.png" alt="PyMesh Demo" width="800">
</a>
<br>
<b><a href="https://pozzettiandrea.github.io/PyMesh/">View Live Demo →</a></b>
</div>

> Fork of [PyMesh/PyMesh](https://github.com/PyMesh/PyMesh) with distributable wheels.

Python bindings for geometry processing: booleans, self-intersection, repair, remeshing, convex hull, outer hull, tetrahedralization, winding numbers.

## Installation

```bash
pip install pymesh2 --find-links https://github.com/PozzettiAndrea/PyMesh/releases/latest/download/
```

## What's Different

This fork applies minimal patches to enable modern builds:

- **Python 3.10–3.13** support (pybind11 v2.13.6)
- **Modern compilers** (GCC 10+, Clang 15+, MSVC 2022)
- **Cross-platform wheels** (Linux, macOS ARM64, Windows)

## License

GPL-3.0 — same as upstream PyMesh.

## Credits

- [PyMesh](https://github.com/PyMesh/PyMesh) by Qingnan Zhou (NYU)
