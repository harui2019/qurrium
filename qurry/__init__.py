"""
================================================================
Qurry 🍛 - The Quantum Experiment Manager for Qiskit 
and The Measuring Tool for Renyi Entropy, Loschmidt Echo, and More
================================================================

## Note for Rust acceleration

### Module import 

> Note that this does not define a package,
> so this won’t allow Python code to directly import submodules
> by using from parent_module import child_module.
> For more information, 
> see [#759](https://github.com/PyO3/pyo3/issues/759) 
> and [#1517](https://github.com/PyO3/pyo3/issues/1517).
from https://pyo3.rs/v0.20.0/module#python-submodules

### Rust availablity

For some platform or environment, there is not Rust acceleration
due to limit to Rust platform support or you install from source without Rust complier
More info see https://github.com/harui2019/qurry/issues/98

So we use optional import here. if Rust is not available, 
the functions used acceleration will run by Cython or Python instead of Rust.

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
    version_check,
    cmdWrapper,
    pytorchCUDACheck,
)

from .version import __version__, __version_str__

# pylint: disable=no-name-in-module,import-error,wrong-import-order,no-member
try:
    import qurry.boorust # type: ignore

    sys.modules["qurry.boorust.construct"] = qurry.boorust.construct # type: ignore
    sys.modules["qurry.boorust.randomized"] = qurry.boorust.randomized # type: ignore
    RUST_AVAILABLE = True
    FAILED_RUST_IMPORT = None
except ModuleNotFoundError as qurry_boorust_import_error:
    RUST_AVAILABLE = False
    FAILED_RUST_IMPORT = qurry_boorust_import_error

BackendAvailabilities = {
    "Python": True,
    "Rust": RUST_AVAILABLE if RUST_AVAILABLE else FAILED_RUST_IMPORT,
}

# """
# Note that this does not define a package,
# so this won’t allow Python code to directly import submodules
# by using from parent_module import child_module.
# For more information,
# see [#759](https://github.com/PyO3/pyo3/issues/759) and
# [#1517](https://github.com/PyO3/pyo3/issues/1517).
# """
# from https://pyo3.rs/v0.20.0/module#python-submodules
# WTF?

# DO NOT MAKE .pyi FOR boorust MODULES.
# it will overwrite and corrupt the module from rust.

# pylint: enable=no-name-in-module,import-error,wrong-import-order,no-member
