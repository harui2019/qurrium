"""
================================================================
Qurry 🍛 - The Quantum Experiment Manager for Qiskit 
and The Measuring Tool for Renyi Entropy, Loschmidt Echo, and More
================================================================

"""
import sys

from .qurmagsq import MagnetSquare
from .qurrech import EchoListen
from .qurrent import EntropyMeasure
# from .qurstrop import StringOperator
from .qurrium import QurryV5 as Qurry, WavesExecuter
# from .recipe import Qurecipe

from .tools import (
    BackendWrapper,
    BackendManager,
    ResoureWatch,
    version_check,
    cmdWrapper,
    pytorchCUDACheck,
)

from .version import __version__, __version_str__

# pylint: disable=no-name-in-module,import-error,wrong-import-order,no-member
import qurry.boorust
sys.modules['qurry.boorust.construct'] = qurry.boorust.construct
sys.modules['qurry.boorust.randomized'] = qurry.boorust.randomized

# """
# Note that this does not define a package,
# so this won’t allow Python code to directly import submodules
# by using from parent_module import child_module.
# For more information, see #759 and #1517.
# """
# from https://pyo3.rs/v0.20.0/module#python-submodules
# WTF?

# DO NOT MAKE .pyi FOR boorust MODULES.
# it will overwrite and corrupt the module from rust.

# pylint: enable=no-name-in-module,import-error,wrong-import-order,no-member
