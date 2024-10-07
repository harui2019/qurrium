"""
================================================================
Setup Script for Qurry
================================================================

"""

import os
from setuptools import setup
from setuptools_rust import Binding, RustExtension


rust_extension = [
    RustExtension(
        "qurry.boorust",
        "crates/boorust/Cargo.toml",
        binding=Binding.PyO3,
        optional=True,
    )
]

with open(os.path.join("qurry", "VERSION.txt"), encoding="utf-8") as version_file:
    __version__ = version_file.read().strip()

print(f"| Version: {__version__}")


setup(
    version=__version__,
    rust_extensions=rust_extension,
    # options={"bdist_wheel": {"py_limited_api": "cp39"}},
)
