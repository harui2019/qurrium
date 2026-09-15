"""Qurrium - The Quantum Experiment Manager for Qiskit
and The Measuring Tool for Renyi Entropy, Loschmidt Echo, and More

"""

import importlib.util
import sys
from importlib.machinery import EXTENSION_SUFFIXES
from pathlib import Path

# =============================================================================
# About the possible conflict between the stub and the compiled extension
# =============================================================================
# `from . import boorust` resolves relative to this source directory first.
# In CI (e.g. GitHub Actions), after `cibuildwheel` + `pip install dist/*.whl`,
# the compiled .so lands in site-packages, but tests are run from the source tree.
# Python then finds the Python fallback stub under qurry/boorust/ instead of the
# real .so, silently missing all Rust-accelerated implementations.
# Fix: import whatever `from .` gives us, check if it is actually a compiled
# extension, and if not, search sys.path for the .so installed elsewhere.
from . import boorust as _boorust


# pylint: disable=wrong-import-position
def _load_boorust_extension():
    """Load boorust extension module from installed site-packages when available."""
    current_package_dir = Path(__file__).resolve().parent

    for search_root in (Path(p) for p in sys.path if isinstance(p, str) and p):
        candidate_dir = search_root / "qurry"
        if not candidate_dir.exists():
            continue
        if candidate_dir.resolve() == current_package_dir:
            continue

        for suffix in EXTENSION_SUFFIXES:
            candidate = candidate_dir / f"boorust{suffix}"
            if not candidate.exists():
                continue

            spec = importlib.util.spec_from_file_location("qurry.boorust", candidate)
            if spec is None or spec.loader is None or not hasattr(spec.loader, "exec_module"):
                continue

            module = importlib.util.module_from_spec(spec)
            previous_module = sys.modules.get("qurry.boorust")
            sys.modules["qurry.boorust"] = module
            try:
                spec.loader.exec_module(module)
            except (ImportError, OSError):  # ABI mismatch, missing deps, or file-level race
                if previous_module is None:
                    sys.modules.pop("qurry.boorust", None)
                else:
                    sys.modules["qurry.boorust"] = previous_module
                continue
            return module

    return _boorust


def _is_boorust_extension(module):
    # True only when __file__ ends with a platform extension suffix
    # e.g. .cpython-312-x86_64-linux-gnu.so
    module_file = getattr(module, "__file__", "") or ""
    return any(module_file.endswith(suffix) for suffix in EXTENSION_SUFFIXES)


# Use the stub-imported _boorust only if it is the real compiled extension.
boorust = _boorust if _is_boorust_extension(_boorust) else _load_boorust_extension()

# =============================================================================
# Manual assignment of boorust submodules to sys.modules
# =============================================================================
# Due to PyO3 submodule is not fully compatible as a Python module.
# So we will need to assign them manually like the following does.
# Qiskit also does something similar which I 'learned' from them at beginning.
# They do not create stub for their Rust binding, but I made it here.
# But stub got other issues, refer to the comments above:
# "About the possible conflict between the stub and the compiled extension"
for boorust_submodule in (
    "counts_process",
    "bit_slice",
    "randomized",
    "hadamard",
    "magnet_square",
    "string_operator",
    "shadow",
    "dummy",
):
    boorust_module = getattr(boorust, boorust_submodule, None)
    if boorust_module is not None:
        sys.modules[f"qurry.boorust.{boorust_submodule}"] = boorust_module  # type: ignore

from .qurries import (
    EntropyMeasure,
    EchoListen,
    WaveFunctionOverlap,
    WavesExecuter,
    SamplingExecuter,
    MagnetSquare,
    ZDirMagnetSquare,
    StringOperator,
    ShadowUnveil,
)
from .tools import (
    get_qiskit_version_statesheet,
    cmd_wrapper,
    pytorch_cuda_check,
    fun_platform_check,
)
from .process.randomized_measure import generate_random_unitary_seeds, check_random_unitary_seeds
from .process.classical_shadow import generate_random_basis, check_random_basis
from .process.availability import availability
from .version import __version__


BACKEND_AVAILABLE = availability("boorust", [("Rust", True, None)])
