import os
from setuptools import setup, find_packages, Extension
from distutils.util import convert_path


def re_cythonize(extensions, **kwargs):
    try:
        from Cython.Build import cythonize
        return cythonize(extensions, **kwargs)
    except ImportError:
        print("| Cython is not installed.")
        print("| Please install cython manually at first,")
        print("| Then reinstall qurry for more powerful performance.")


cy_extensions = [
    Extension(
        "qurry.boost.randomized",
        ["qurry/boost/randomized.pyx"]),
    Extension(
        "qurry.boost.inputfixer",
        ["qurry/boost/inputfixer.pyx"]),
]


main_ns = {}
ver_path = convert_path('./qurry/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

__version_str__ = main_ns['__version_str__']
print(f'| Version: {__version_str__}')

README_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'README.md')
with open(README_PATH) as readme_file:
    README = readme_file.read()

# qiskit_main = [
#     # qiskit ibmq provider dedicated
#     "requests~=2.28.0",
#     "numpy<1.24",
#     "python-dateutil==2.8.0",
#     "requests-ntlm==1.1.0",
#     "websocket-client>=1.5.1",
#     "websockets==10.0 ; python_version>='3.7'",
#     "websockets>=9.1 ; python_version<'3.7'",
#     "dataclasses>=0.8 ; python_version<'3.7'",

#     "qiskit==0.41.1",
#     "qiskit-aer==0.11.2",
#     "qiskit-ibm-provider==0.4.0",
#     "qiskit-terra==0.23.2",
#     "qiskit-ibmq-provider==0.20.1"
# ]
# qiskit_gpu = [
#     # https://peps.python.org/pep-0508/
#     "qiskit-aer-gpu; platform_system=='Linux'",
# ]
# bugfix = [
#     # "urllib3==1.22",
# ]
# dependencies = [
#     "cython",
#     "tqdm",
#     "matplotlib",
# ]

# requirement = qiskit_main + qiskit_gpu + bugfix + dependencies
install_requires = [
    "qiskit>=0.32.2",
    "qiskit-aer>=0.9.1",
    "cython",
    "tqdm",
    "matplotlib",
]

__author__ = "Huai-Chung Chang (harui2019@proton.me)"


setup(
    name='qurry',
    version=__version_str__,
    description='Qurry 🍛 - The Measuring Tool for Renyi Entropy, Loschmidt Echo, and Magnetization Squared, The Library of Some Common Cases',
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

    install_requires=install_requires,
    python_requires=">=3.9",
)
