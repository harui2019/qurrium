"""
=========================================================================================
Postprocessing - Randomized Measure - Wavefunction Overlap - Echo Cell
(:mod:`qurry.process.randomized_measure.wavefunction_overlap.echo_cell`)
=========================================================================================

"""

import warnings
from typing import Union
import numpy as np

from ...utils import ensemble_cell as ensemble_cell_py, cycling_slice as cycling_slice_py
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
    from ...boorust import randomized  # type: ignore

    echo_cell_rust_source = randomized.echo_cell_rust

    RUST_AVAILABLE = True
    FAILED_RUST_IMPORT = None
except ImportError as err:
    RUST_AVAILABLE = False
    FAILED_RUST_IMPORT = err

    def echo_cell_rust_source(*args, **kwargs):
        """Dummy function for cho_cell_rust."""
        raise PostProcessingRustImportError(
            "Rust is not available, using python to calculate purity cell."
        ) from FAILED_RUST_IMPORT


BACKEND_AVAILABLE = availablility(
    "randomized_measure.echo_cell",
    [
        ("Rust", RUST_AVAILABLE, FAILED_RUST_IMPORT),
        ("Cython", "Depr.", None),
    ],
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(
    RUST_AVAILABLE,
    False,
)


def echo_cell_rust(
    idx: int,
    first_counts: dict[str, int],
    second_counts: dict[str, int],
    bitstring_range: tuple[int, int],
    subsystem_size: int,
) -> tuple[int, float]:
    """Calculate the echo cell, one of overlap, of a subsystem by Rust.

    Args:
        idx (int): Index of the cell (counts).
        first_counts (dict[str, int]): Counts measured by the first quantum circuit.
        second_counts (dict[str, int]): Counts measured by the second quantum circuit.
        bitstring_range (tuple[int, int]): The range of the subsystem.
        subsystem_size (int): Subsystem size included.

    Returns:
        tuple[int, float]: Index, one of overlap purity.
    """
    return idx, echo_cell_rust_source(first_counts, second_counts, bitstring_range, subsystem_size)


def echo_cell_py(
    idx: int,
    first_counts: dict[str, int],
    second_counts: dict[str, int],
    bitstring_range: tuple[int, int],
    subsystem_size: int,
) -> tuple[int, np.float64]:
    """Calculate the echo cell, one of overlap, of a subsystem by Python.

    Args:
        idx (int): Index of the cell (counts).
        first_counts (dict[str, int]): Counts measured by the first quantum circuit.
        second_counts (dict[str, int]): Counts measured by the second quantum circuit.
        bitstring_range (tuple[int, int]): The range of the subsystem.
        subsystem_size (int): Subsystem size included.

    Returns:
        tuple[int, float]: Index, one of overlap purity.
    """

    shots = sum(first_counts.values())
    shots2 = sum(second_counts.values())
    assert shots == shots2, f"shots {shots} does not match shots2 {shots2}"

    _dummy_string = list(range(len(list(first_counts.keys())[0])))
    _dummy_string2 = list(range(len(list(second_counts.keys())[0])))
    assert (
        _dummy_string == _dummy_string2
    ), f"first_counts {first_counts} != second_counts {second_counts}"

    if _dummy_string[bitstring_range[0] : bitstring_range[1]] == cycling_slice_py(
        _dummy_string, bitstring_range[0], bitstring_range[1], 1
    ):
        first_counts_under_degree = dict.fromkeys(
            [k[bitstring_range[0] : bitstring_range[1]] for k in first_counts], 0
        )
        for bitstring in list(first_counts):
            first_counts_under_degree[
                bitstring[bitstring_range[0] : bitstring_range[1]]
            ] += first_counts[bitstring]

        second_counts_under_degree = dict.fromkeys(
            [k[bitstring_range[0] : bitstring_range[1]] for k in second_counts], 0
        )
        for bitstring in list(second_counts):
            second_counts_under_degree[
                bitstring[bitstring_range[0] : bitstring_range[1]]
            ] += second_counts[bitstring]
    else:
        first_counts_under_degree = dict.fromkeys(
            [cycling_slice_py(k, bitstring_range[0], bitstring_range[1], 1) for k in first_counts],
            0,
        )
        for bitstring in list(first_counts):
            first_counts_under_degree[
                cycling_slice_py(bitstring, bitstring_range[0], bitstring_range[1], 1)
            ] += first_counts[bitstring]

        second_counts_under_degree = dict.fromkeys(
            [cycling_slice_py(k, bitstring_range[0], bitstring_range[1], 1) for k in second_counts],
            0,
        )
        for bitstring in list(second_counts):
            second_counts_under_degree[
                cycling_slice_py(bitstring, bitstring_range[0], bitstring_range[1], 1)
            ] += second_counts[bitstring]

    _echo_cell = np.float64(0)
    for s_i, s_i_meas in first_counts_under_degree.items():
        for s_j, s_j_meas in second_counts_under_degree.items():
            _echo_cell += ensemble_cell_py(s_i, s_i_meas, s_j, s_j_meas, subsystem_size, shots)

    return idx, _echo_cell


def echo_cell(
    idx: int,
    first_counts: dict[str, int],
    second_counts: dict[str, int],
    bitstring_range: tuple[int, int],
    subsystem_size: int,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[int, Union[float, np.float64]]:
    """Calculate the echo cell, one of overlap, of a subsystem.

    Args:
        idx (int): Index of the cell (counts).
        first_counts (dict[str, int]): Counts measured by the first quantum circuit.
        second_counts (dict[str, int]): Counts measured by the second quantum circuit.
        bitstring_range (tuple[int, int]): The range of the subsystem.
        subsystem_size (int): Subsystem size included.

    Returns:
        tuple[int, float]: Index, one of overlap purity.
    """
    if not RUST_AVAILABLE and backend == "Rust":
        warnings.warn(
            "Rust is not available, using Cython or Python to calculate purity cell."
            + f"Check the error: {FAILED_RUST_IMPORT}",
            PostProcessingRustUnavailableWarning,
        )
        backend = "Python"

    if backend == "Rust":
        return echo_cell_rust(idx, first_counts, second_counts, bitstring_range, subsystem_size)
    return echo_cell_py(idx, first_counts, second_counts, bitstring_range, subsystem_size)
