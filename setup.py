"""
================================================================
Setup Script for Qurry
================================================================

"""
from pathlib import Path
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

allowed_globals = {}
allow_locals = {}
ver_path = Path("./qurry/version.py")
with open(ver_path, encoding="utf-8") as ver_file:
    # pylint: disable-next=exec-used
    exec(ver_file.read(), allowed_globals, allow_locals)
    # pylint: disable-next=exec-used

__version_str__ = allow_locals["__version_str__"]
print(f"| Version: {__version_str__}")


setup(
    version=__version_str__,
    ext_modules=re_cythonize(
        cy_extensions,
        language_level=3,
    ),
    rust_extensions=rust_extension,
)
