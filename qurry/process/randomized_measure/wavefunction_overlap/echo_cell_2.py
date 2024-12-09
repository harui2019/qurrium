"""
=========================================================================================
Postprocessing - Randomized Measure - Wavefunction Overlap - Echo Cell 2
(:mod:`qurry.process.randomized_measure.wavefunction_overlap.echo_cell_2`)
=========================================================================================

"""

import warnings
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
)


try:
    from ....boorust import randomized  # type: ignore

    echo_cell_2_rust_source = randomized.echo_cell_2_rust

    RUST_AVAILABLE = True
    FAILED_RUST_IMPORT = None
except ImportError as err:
    RUST_AVAILABLE = False
    FAILED_RUST_IMPORT = err

    def echo_cell_2_rust_source(*args, **kwargs):
        """Dummy function for cho_cell_rust."""
        raise PostProcessingRustImportError(
            "Rust is not available, using python to calculate purity cell."
        ) from FAILED_RUST_IMPORT


BACKEND_AVAILABLE = availablility(
    "randomized_measure.wavefunction_overlap.echo_cell_2",
    [
        ("Rust", RUST_AVAILABLE, FAILED_RUST_IMPORT),
        ("Cython", "Depr.", None),
    ],
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(
    RUST_AVAILABLE,
    False,
)


def echo_cell_2_py(
    idx: int,
    first_counts: dict[str, int],
    second_counts: dict[str, int],
    selected_classical_registers: list[int],
) -> tuple[int, np.float64, list[int]]:
    """Calculate the echo cell, one of overlap, of a subsystem by Python.

    Args:
        idx (int):
            Index of the cell (counts).
        first_counts (dict[str, int]):
            Counts measured from the first quantum circuit.
        second_counts (dict[str, int]):
            Counts measured from the second quantum circuit.
        selected_classical_registers (list[int]):
            The list of **the index of the selected_classical_registers**.

    Returns:
        tuple[int, float, list[int]]:
            Index, one of overlap purity,
            The list of **the index of the selected classical registers**.
    """

    num_classical_register = len(list(first_counts.keys())[0])
    num_classical_register_02 = len(list(second_counts.keys())[0])
    assert num_classical_register == num_classical_register_02, (
        "The number of classical registers from the first and second counts are different. "
        + f"first: {num_classical_register}, second: {num_classical_register_02}"
    )

    shots = sum(first_counts.values())
    shots_02 = sum(second_counts.values())
    assert shots == shots_02, (
        "The shots from the first and second counts are different. "
        + f"first: {shots}, second: {shots_02}"
    )
    selected_classical_registers_sorted = sorted(selected_classical_registers, reverse=True)
    subsystem_size = len(selected_classical_registers_sorted)

    first_counts_under_degree = {}
    for bitstring_all, num_counts_all in first_counts.items():
        bitstring = "".join(
            bitstring_all[num_classical_register - q_i - 1]
            for q_i in selected_classical_registers_sorted
        )
        if bitstring in first_counts_under_degree:
            first_counts_under_degree[bitstring] += num_counts_all
        else:
            first_counts_under_degree[bitstring] = num_counts_all
    second_counts_under_degree = {}
    for bitstring_all, num_counts_all in second_counts.items():
        bitstring = "".join(
            bitstring_all[num_classical_register - q_i - 1]
            for q_i in selected_classical_registers_sorted
        )
        if bitstring in second_counts_under_degree:
            second_counts_under_degree[bitstring] += num_counts_all
        else:
            second_counts_under_degree[bitstring] = num_counts_all

    echo_cell_value = np.float64(0)
    for s_ai, s_ai_meas in first_counts_under_degree.items():
        for s_aj, s_aj_meas in second_counts_under_degree.items():
            echo_cell_value += ensemble_cell_py(
                s_ai, s_ai_meas, s_aj, s_aj_meas, subsystem_size, shots
            )

    return idx, echo_cell_value, selected_classical_registers_sorted


def echo_cell_2_rust(
    idx: int,
    first_counts: dict[str, int],
    second_counts: dict[str, int],
    selected_classical_registers: list[int],
) -> tuple[int, np.float64, list[int]]:
    """Calculate the echo cell, one of overlap, of a subsystem by Rust.

    Args:
        idx (int):
            Index of the cell (counts).
        first_counts (dict[str, int]):
            Counts measured from the first quantum circuit.
        second_counts (dict[str, int]):
            Counts measured from the second quantum circuit.
        selected_classical_registers (list[int]):
            The list of **the index of the selected_classical_registers**.

    Returns:
        tuple[int, float, list[int]]:
            Index, one of overlap purity,
            The list of **the index of the selected classical registers**.
    """
    return echo_cell_2_rust_source(idx, first_counts, second_counts, selected_classical_registers)


def echo_cell_2(
    idx: int,
    first_counts: dict[str, int],
    second_counts: dict[str, int],
    selected_classical_registers: list[int],
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[int, np.float64, list[int]]:
    """Calculate the echo cell, one of overlap, of a subsystem.
    Args:
        idx (int):
            Index of the cell (counts).
        first_counts (dict[str, int]):
            Counts measured from the first quantum circuit.
        second_counts (dict[str, int]):
            Counts measured from the second quantum circuit.
        selected_classical_registers (list[int]):
            The list of **the index of the selected_classical_registers**.

    Returns:
        tuple[int, float, list[int]]:
            Index, one of overlap purity,
            The list of **the index of the selected classical registers**.
    """
    if not RUST_AVAILABLE and backend == "Rust":
        warnings.warn(
            "Rust is not available, using Cython or Python to calculate purity cell."
            + f"Check the error: {FAILED_RUST_IMPORT}",
            PostProcessingRustUnavailableWarning,
        )
        backend = "Python"

    if backend == "Rust":
        return echo_cell_2_rust(idx, first_counts, second_counts, selected_classical_registers)
    return echo_cell_2_py(idx, first_counts, second_counts, selected_classical_registers)
