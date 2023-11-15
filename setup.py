"""
================================================================
Setup Script for Qurry
================================================================

"""
import os
from pathlib import Path
from setuptools import setup, find_packages, Extension
from setuptools_rust import Binding, RustExtension

with open("requirements.txt", encoding="utf-8") as f:
    REQUIREMENTS = f.read().splitlines()


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

README_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "README.md")
with open(README_PATH, encoding="utf-8") as readme_file:
    README = readme_file.read()

__author__ = "Huai-Chung Chang (harui2019@proton.me)"


setup(
    name="qurry",
    version=__version_str__,
    description=(
        "Qurry 🍛 - The Measuring Tool for Renyi Entropy, Loschmidt Echo, "
        + "and Magnetization Squared, The Library of Some Common Cases"
    ),
    long_description=README,
    long_description_content_type="text/markdown",
    classifiers=[
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    project_urls={
        "Bug Tracker": "https://github.com/harui2019/qurry/issues",
        "Homepage": "https://github.com/harui2019/qurry",
    },
    url="https://github.com/harui2019/qurry",
    author="Huai-Chung Chang",
    author_email="harui2019@proton.me",
    packages=find_packages(
        include=["qurry*", "qurry.capsule*"],
        exclude=["cmake", "symengine", "tests"],
    ),
    include_package_data=True,
    ext_modules=re_cythonize(
        cy_extensions,
        language_level=3,
    ),
    rust_extensions=rust_extension,
    install_requires=REQUIREMENTS,
    python_requires=">=3.9",
)
