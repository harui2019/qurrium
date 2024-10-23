"""
================================================================
Postprocessing - Hadamard Test - Purity/Echo
(:mod:`qurry.process.hadamard_test.purity_echo_core`)
================================================================

"""

import warnings
import numpy as np

from ..availability import (
    availablility,
    default_postprocessing_backend,
    PostProcessingBackendLabel,
)
from ..exceptions import (
    PostProcessingRustImportError,
    PostProcessingRustUnavailableWarning,
    PostProcessingBackendDeprecatedWarning,
)

try:
    from ...boorust import hadamard  # type: ignore

    purity_echo_core_rust_source = hadamard.purity_echo_core_rust

    RUST_AVAILABLE = True
    FAILED_RUST_IMPORT = None
except ImportError as err:
    RUST_AVAILABLE = False
    FAILED_RUST_IMPORT = err

    def purity_echo_core_rust_source(*args, **kwargs):
        """Dummy function for purity_cell_rust."""
        raise PostProcessingRustImportError(
            "Rust is not available, using python to calculate purity cell."
        ) from FAILED_RUST_IMPORT


BACKEND_AVAILABLE = availablility(
    "hadamard_test.purity_echo_core",
    [
        ("Rust", RUST_AVAILABLE, FAILED_RUST_IMPORT),
    ],
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(
    RUST_AVAILABLE,
    False,
)


def purity_echo_core_allrust(
    shots: int,
    counts: list[dict[str, int]],
) -> float:
    """The core function of entangled entropy by Rust.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.

    Raises:
        ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
        ValueError: Measure range does not contain subsystem.

    Returns:
        float: Purity or Echo of the experiment.
    """

    return purity_echo_core_rust_source(shots, counts)


def purity_echo_core(
    shots: int,
    counts: list[dict[str, int]],
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> float:
    """Calculate entangled entropy with more information combined.

    - Which entropy:

        The entropy we compute is the Second Order Rényi Entropy.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.

    Raises:
        Warning: Expected '0' and '1', but there is no such keys

    Returns:
        dict[str, float]: Quantity of the experiment.
    """

    if backend == "Rust":
        if RUST_AVAILABLE:
            return purity_echo_core_allrust(shots, counts)

        warnings.warn(
            PostProcessingRustUnavailableWarning(
                "Rust is not available, using python to calculate purity cell."
            )
        )
    if backend == "Cython":
        warnings.warn(
            "Cython backend is deprecated, using Python or Rust to calculate purity cell.",
            PostProcessingBackendDeprecatedWarning,
        )
        backend = DEFAULT_PROCESS_BACKEND

    only_counts = counts[0]
    sample_shots = sum(only_counts.values())
    assert sample_shots == shots, f"shots {shots} does not match sample_shots {sample_shots}"

    is_zero_include = "0" in only_counts
    is_one_include = "1" in only_counts
    if is_zero_include and is_one_include:
        purity = (only_counts["0"] - only_counts["1"]) / shots
    elif is_zero_include:
        purity = only_counts["0"] / shots
    elif is_one_include:
        purity = only_counts["1"] / shots
    else:
        purity = np.nan
        raise ValueError("Expected '0' and '1', but there is no such keys")

    return purity
