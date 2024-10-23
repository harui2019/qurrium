"""
=========================================================================================
Postprocessing - Randomized Measure - Entangled Entropy - Purity Cell 2
(:mod:`qurry.process.randomized_measure.entangled_entropy.purity_cell_2`)
=========================================================================================

This version introduces another way to process subsystems.

"""

import warnings
from typing import Union
import numpy as np

from ...utils import ensemble_cell as ensemble_cell_py
from ...availability import (
    availablility,
    default_postprocessing_backend,
    PostProcessingBackendLabel,
)
from ...exceptions import (
    PostProcessingRustImportError,
    PostProcessingRustUnavailableWarning,
    PostProcessingBackendDeprecatedWarning,
)


try:

    from ....boorust import randomized  # type: ignore

    purity_cell_2_rust_source = randomized.purity_cell_2_rust

    RUST_AVAILABLE = True
    FAILED_RUST_IMPORT = None
except ImportError as err:
    RUST_AVAILABLE = False
    FAILED_RUST_IMPORT = err

    def purity_cell_rust_source(*args, **kwargs):
        """Dummy function for purity_cell_rust."""
        raise PostProcessingRustImportError(
            "Rust is not available, using python to calculate purity cell."
        ) from FAILED_RUST_IMPORT


BACKEND_AVAILABLE = availablility(
    "randomized_measure.entangle_entropy.purity_cell_2",
    [
        ("Rust", RUST_AVAILABLE, FAILED_RUST_IMPORT),
        ("Cython", "Depr.", None),
    ],
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(RUST_AVAILABLE, False)


# Randomized measure
def purity_cell_2_py(
    idx: int,
    single_counts: dict[str, int],
    selected_classical_registers: list[int],
) -> tuple[int, np.float64, list[int]]:
    """Calculate the purity cell, one of overlap, of a subsystem by Python.

    Args:
        idx (int):
            Index of the cell (counts).
        single_counts (dict[str, int]):
            Counts measured by the single quantum circuit.
        selected_classical_registers (list[int]):
            The list of **the index of the selected_classical_registers**.

    Returns:
        tuple[int, float, list[int]]:
            Index, one of overlap purity,
            The list of **the index of the selected classical registers**.
    """

    num_classical_register = len(list(single_counts.keys())[0])
    shots = sum(single_counts.values())

    selected_classical_registers_sorted = sorted(selected_classical_registers, reverse=True)
    subsystem_size = len(selected_classical_registers_sorted)
    single_counts_under_degree = {}
    for bitstring_all, num_counts_all in single_counts.items():
        bitstring = "".join(
            bitstring_all[num_classical_register - q_i - 1]
            for q_i in selected_classical_registers_sorted
        )
        if bitstring in single_counts_under_degree:
            single_counts_under_degree[bitstring] += num_counts_all
        else:
            single_counts_under_degree[bitstring] = num_counts_all

    purity_cell_value = np.float64(0)
    for s_ai, s_ai_meas in single_counts_under_degree.items():
        for s_aj, s_aj_meas in single_counts_under_degree.items():
            purity_cell_value += ensemble_cell_py(
                s_ai, s_ai_meas, s_aj, s_aj_meas, subsystem_size, shots
            )

    return idx, purity_cell_value, selected_classical_registers_sorted


def purity_cell_2_rust(
    idx: int,
    single_counts: dict[str, int],
    selected_classical_registers: list[int],
) -> tuple[int, np.float64, list[int]]:
    """Calculate the purity cell, one of overlap, of a subsystem by Rust.

    Args:
        idx (int):
            Index of the cell (counts).
        single_counts (dict[str, int]):
            Counts measured by the single quantum circuit.
        selected_classical_registers (list[int]):
            The list of **the index of the selected_classical_registers**.

    Returns:
        tuple[int, float, list[int]]:
            Index, one of overlap purity,
            The list of **the index of the selected classical registers**.
    """

    return purity_cell_2_rust_source(idx, single_counts, selected_classical_registers)


def purity_cell_2(
    idx: int,
    single_counts: dict[str, int],
    selected_classical_registers: list[int],
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[int, Union[float, np.float64], list[int]]:
    """Calculate the purity cell, one of overlap, of a subsystem.

    Args:
        idx (int):
            Index of the cell (counts).
        single_counts (dict[str, int]):
            Counts measured by the single quantum circuit.
        selected_bitstrings (list[int]):
            The list of **the index of the selected classical registers**.
        backend (ExistingProcessBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.

    Returns:
        tuple[int, Union[float, np.float64], list[int]]:
            Index, one of overlap purity,
            The list of **the index of the selected classical registers**.
    """

    if backend == "Cython":
        warnings.warn(
            f"The Cython is deprecated, using {DEFAULT_PROCESS_BACKEND} to calculate purity cell.",
            PostProcessingBackendDeprecatedWarning,
        )
        backend = DEFAULT_PROCESS_BACKEND
    if backend == "Rust":
        if RUST_AVAILABLE:
            return purity_cell_2_rust(idx, single_counts, selected_classical_registers)
        warnings.warn(
            "Rust is not available, using Python to calculate purity cell."
            + f"Check the error: {FAILED_RUST_IMPORT}",
            PostProcessingRustUnavailableWarning,
        )
        backend = "Python"

    return purity_cell_2_py(idx, single_counts, selected_classical_registers)
