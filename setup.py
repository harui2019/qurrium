import os
from setuptools import setup, find_packages

README_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'README.md')
with open(README_PATH) as readme_file:
    README = readme_file.read()
    
qiskit_main = [
    "qiskit==0.39.2",
    "qiskit-terra==0.22.2",
    "qiskit-aer==0.11.1",
    "qiskit-ibmq-provider==0.19.2",
]
qiskit_gpu = [
    "qiskit-aer-gpu; platform_system=='Linux' and python_version<='3.9'", # https://peps.python.org/pep-0508/
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
    version='0.5.0.beta01',
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