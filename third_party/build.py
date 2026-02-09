#!/usr/bin/env python

""" Build and install third party dependencies for PyMesh.
"""

import argparse
import subprocess
import os
import os.path
import tempfile
import shutil
import sys

def get_third_party_dependencies():
    return ["cgal", "cork", "eigen",
        "tetgen", "triangle", "qhull", "clipper", "draco",
        "tbb", "mmg", "json"]

def parse_args():
    parser = argparse.ArgumentParser(__doc__);
    parser.add_argument("--cleanup", action="store_true",
            help="Clean up the build folder after done.");
    parser.add_argument("package",
            choices=["all"] + get_third_party_dependencies());
    return parser.parse_args();

def get_pymesh_dir():
    return os.path.join(sys.path[0], "..");

def ninja_available():
    """Check if ninja is available on the system."""
    try:
        subprocess.check_call(["ninja", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def is_already_built(libname):
    """Check if library is already built (for cache support)."""
    pymesh_dir = get_pymesh_dir()
    install_dir = os.path.join(pymesh_dir, "python", "pymesh", "third_party")

    # Check for marker files indicating successful build
    markers = {
        "cgal": "include/CGAL/version.h",
        "cork": "lib/libcork.a",
        "eigen": "include/eigen3/Eigen/Core",
        "tetgen": "lib/libtet.a",
        "triangle": "lib/libtriangle.a",
        "qhull": "include/libqhull_r/qhull_ra.h",
        "clipper": "lib/libpolyclipping.a",
        "draco": "include/draco/core/draco_version.h",
        "tbb": "lib/libtbb.a",  # Check for library, not just header
        "mmg": "include/mmg/mmg3d/libmmg3d.h",
        "json": "include/nlohmann/json.hpp",
    }

    # Handle special cases
    if libname == "Clipper/cpp":
        libname = "clipper"

    marker = markers.get(libname)
    if marker:
        marker_path = os.path.join(install_dir, marker)
        if os.path.exists(marker_path):
            print(f"[CACHE] {libname} already built, skipping...")
            return True
    return False

def build_generic(libname, build_flags="", cleanup=True):
    # Skip if already built (cache hit)
    if is_already_built(libname):
        return

    pymesh_dir = get_pymesh_dir();
    build_dir = os.path.join(pymesh_dir, "third_party", "build", libname);
    if not os.path.exists(build_dir):
        os.makedirs(build_dir);

    # On Windows, use Visual Studio generator (MSVC) for compatibility with vcpkg
    # On other platforms, use Ninja if available for faster builds
    source_dir = "{}/third_party/{}".format(pymesh_dir, libname)
    install_prefix = "{}/python/pymesh/third_party/".format(pymesh_dir)

    if sys.platform == "win32":
        # Build command as list to handle spaces in generator name
        configure_cmd = [
            "cmake", source_dir,
            "-G", "Visual Studio 17 2022",
            "-A", "x64",
            "-DBUILD_SHARED_LIBS=Off",
            "-DCMAKE_POSITION_INDEPENDENT_CODE=On",
            "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
            "-DCMAKE_INSTALL_PREFIX={}".format(install_prefix),
        ] + (build_flags.split() if build_flags else [])
    else:
        generator_flag = "-GNinja" if ninja_available() else ""
        configure_cmd = [
            "cmake", source_dir,
        ] + ([generator_flag] if generator_flag else []) + [
            "-DBUILD_SHARED_LIBS=Off",
            "-DCMAKE_POSITION_INDEPENDENT_CODE=On",
            "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
            "-DCMAKE_INSTALL_PREFIX={}".format(install_prefix),
        ] + (build_flags.split() if build_flags else [])

    subprocess.check_call(configure_cmd, cwd=build_dir)

    # Build (with parallel jobs) - add --config Release for MSVC multi-config generators
    build_cmd = ["cmake", "--build", build_dir, "--config", "Release", "--parallel"]
    subprocess.check_call(build_cmd)

    install_cmd = ["cmake", "--build", build_dir, "--config", "Release", "--target", "install"]
    subprocess.check_call(install_cmd)

    # Clean up
    if cleanup:
        shutil.rmtree(build_dir)

def build(package, cleanup):
    if package == "all":
        for libname in get_third_party_dependencies():
            build(libname, cleanup);
    elif package == "cgal":
        # On Windows, skip building CGAL from third_party - use vcpkg's CGAL instead
        # The old third_party CGAL headers are incompatible with vcpkg's newer Boost
        if sys.platform == "win32":
            print("[SKIP] Skipping CGAL on Windows - using vcpkg's CGAL instead")
            return
        build_generic("cgal",
                " -DWITH_CGAL_ImageIO=Off -DWITH_CGAL_Qt5=Off",
                cleanup=cleanup);
    elif package == "qhull":
        build_generic("qhull", cleanup=cleanup);
    elif package == "clipper":
        build_generic("Clipper/cpp", cleanup=cleanup);
    elif package == "tbb":
        # On Windows, skip building TBB from third_party - use vcpkg's TBB instead
        # vcpkg's TBB is compiled with /MD runtime which matches our build
        if sys.platform == "win32":
            print("[SKIP] Skipping TBB on Windows - using vcpkg's TBB instead")
            return
        # Build static to avoid delocate issues with shared lib deps
        build_generic("tbb",
                " -DTBB_BUILD_SHARED=Off -DTBB_BUILD_STATIC=On",
                cleanup=cleanup);
    elif package == "json":
        build_generic("json",
                " -DJSON_BuildTests=Off",
                cleanup=cleanup);
    elif package == "mmg":
        mmg_flags = ""
        if sys.platform == "win32":
            # Windows/MSVC: math is in C runtime, set M_LIB empty to avoid NOTFOUND
            mmg_flags = " -DM_LIB:FILEPATH="
        build_generic("mmg", mmg_flags, cleanup=cleanup);
    else:
        build_generic(package, cleanup=cleanup);

def main():
    args = parse_args();
    build(args.package, args.cleanup);

if __name__ == "__main__":
    main();
