import os
from setuptools import setup, find_packages

from distutils.util import convert_path

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

qiskit_main = [
    # qiskit ibmq provider dedicated
    "requests~=2.28.0",
    "numpy<1.24",
    "urllib3~=1.26.0",
    "python-dateutil==2.8.0",
    "requests-ntlm==1.1.0",
    "numpy<1.24",
    "websocket-client>=1.5.1",
    "websockets==10.0 ; python_version>='3.7'",
    "websockets>=9.1 ; python_version<'3.7'",
    "dataclasses>=0.8 ; python_version<'3.7'",
    
    "qiskit==0.41.1",
    "qiskit-aer==0.11.2",
    "qiskit-ibm-provider==0.4.0",
    "qiskit-ibmq-provider==0.20.1",
    "qiskit-terra==0.23.2"
]
qiskit_gpu = [
    # https://peps.python.org/pep-0508/
    "qiskit-aer-gpu; platform_system=='Linux' and python_version<='3.9'",
]
bugfix = [
    "urllib3==1.22",
]
dependencies = [
    "tqdm",
    "dask",
    "matplotlib",
]

requirement = qiskit_main + qiskit_gpu + bugfix + dependencies

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

    install_requires=requirement,
    python_requires=">=3.9",
)
