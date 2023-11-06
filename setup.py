"""
================================================================
Setup Script for Qurry
================================================================

"""
import os
from pathlib import Path
from setuptools import setup, find_packages, Extension
from setuptools_rust import Binding, RustExtension


def re_cythonize(extensions, **kwargs):
    try:
        from Cython.Build import cythonize
        return cythonize(extensions, **kwargs)
    except ImportError:
        print("| Cython is not installed.")
        print("| Please install cython manually at first,")
        print("| Then reinstall qurry for more powerful performance.")


rust_extension = [
    RustExtension(
        "qurry.boorust",
        "crates/boorust/Cargo.toml",
        binding=Binding.PyO3,
    )
]

cy_extensions = [
    Extension(
        "qurry.boost.randomized",
        ["qurry/boost/randomized.pyx"]),
    Extension(
        "qurry.boost.inputfixer",
        ["qurry/boost/inputfixer.pyx"]),
]

main_ns = {}
ver_path = Path('./qurry/version.py')
with open(ver_path, encoding='utf-8') as ver_file:
    exec(ver_file.read(), main_ns)

__version_str__ = main_ns['__version_str__']
print(f'| Version: {__version_str__}')

README_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'README.md')
with open(README_PATH, encoding='utf-8') as readme_file:
    README = readme_file.read()


# requirement = qiskit_main + qiskit_gpu + bugfix + dependencies
install_requires = [
    "qiskit>=0.32.2",
    "qiskit-aer>=0.10.4",
    "tqdm",
    "matplotlib",
    "requests~=2.28.0",
]

__author__ = "Huai-Chung Chang (harui2019@proton.me)"


setup(
    name='qurry',
    version=__version_str__,
    description=(
        'Qurry 🍛 - The Measuring Tool for Renyi Entropy, Loschmidt Echo, '+
        'and Magnetization Squared, The Library of Some Common Cases'
    ),
    long_description=README,
    long_description_content_type='text/markdown',

    url='https://github.com/harui2019/qurry/qurry',
    author='Huai-Chung Chang',
    author_email='harui2019@proton.me',

    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    ext_modules=re_cythonize(
        cy_extensions,
        language_level=3,
    ),
    rust_extensions=rust_extension,

    install_requires=install_requires,
    python_requires=">=3.9",
)
