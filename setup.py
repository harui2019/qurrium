import os
from setuptools import setup, find_packages

from qurry import __version__

README_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'README.md')
with open(README_PATH) as readme_file:
    README = readme_file.read()
    
requirement = [
    "qiskit>=0.35.0",
    "qiskit-aer;platform_system=='Linux'",
]

setup(
    name='qurry',
    version=__version__,
    description='Qurry 🍛 - The Measuring Tool for Renyi Entropy, Loschmidt Echo, and Magnetization Squared, The Library of Some Common Cases',
    long_description=README,
    long_description_content_type='text/markdown',
    
    url='https://github.com/harui2019/qurry/qurry',
    author='Huai-Chung Chang',
    author_email='james880818@gmail.com',
    
    packages=find_packages(),
    include_package_data=True,
    
    install_requires=requirement,
    python_requires=">=3.8",
)