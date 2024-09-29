"""
================================================================
Setup Script for Qurry
================================================================

"""

import os
from setuptools import setup, Extension
from setuptools_rust import Binding, RustExtension


def re_cythonize(extensions, **kwargs) -> list[Extension]:
    """Re-cythonize the extensions.
    To optionally use cython.
    """
    try:
        # pylint: disable=import-outside-toplevel
        from Cython.Build import cythonize

        # pylint: enable=import-outside-toplevel

        return cythonize(extensions, **kwargs)
    except ImportError:
        print("| Cython is not installed.")
        print("| Please install cython manually at first,")
        print("| Then reinstall qurry for more powerful performance.")
        return []


rust_extension = [
    RustExtension(
        "qurry.boorust",
        "crates/boorust/Cargo.toml",
        binding=Binding.PyO3,
        optional=True,
    )
]

cy_extensions = [
    Extension("qurry.boost.randomized", ["qurry/boost/randomized.pyx"]),
    Extension("qurry.boost.inputfixer", ["qurry/boost/inputfixer.pyx"]),
]

with open(os.path.join("qurry", "VERSION.txt"), encoding="utf-8") as version_file:
    __version__ = version_file.read().strip()

print(f"| Version: {__version__}")


setup(
    version=__version__,
    ext_modules=re_cythonize(
        cy_extensions,
        language_level=3,
    ),
    rust_extensions=rust_extension,
    # options={"bdist_wheel": {"py_limited_api": "cp39"}},
)
