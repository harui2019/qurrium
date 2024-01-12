"""
================================================================
Postprocessing - Wavefunction Overlap - Echo Cell
(:mod:`qurry.process.randomized_measure.echo_cell`)
================================================================

"""
import warnings
from typing import Union, Literal
import numpy as np

from ..utils import ensemble_cell as ensemble_cell_py
from ...exceptions import (
    QurryCythonImportError,
    QurryCythonUnavailableWarning,
    # QurryRustImportError,
    # QurryRustUnavailableWarning,
)


try:
    from ..boost.randomized import echoCellCore  # type: ignore

    CYTHON_AVAILABLE = True
    FAILED_PYX_IMPORT = None
except ImportError as err:
    FAILED_PYX_IMPORT = err
    CYTHON_AVAILABLE = False
    # pylint: disable=invalid-name, unused-argument

    def echoCellCore(*args, **kwargs):
        """Dummy function for purityCellCore."""
        raise QurryCythonImportError(
            "Cython is not available, using python to calculate purity cell."
        ) from FAILED_PYX_IMPORT

    # pylint: enable=invalid-name, unused-argument

# try:
#     from ...boorust import randomized  # type: ignore

#     purity_cell_rust_source = randomized.echo_cell_rust

#     RUST_AVAILABLE = True
#     FAILED_RUST_IMPORT = None
# except ImportError as err:
#     RUST_AVAILABLE = False
#     FAILED_RUST_IMPORT = err

#     def purity_cell_rust_source(*args, **kwargs):
#         """Dummy function for purity_cell_rust."""
#         raise QurryRustImportError(
#             "Rust is not available, using python to calculate purity cell."
#         ) from FAILED_RUST_IMPORT


ExistingProcessBackendLabel = Literal["Cython", "Rust", "Python"]
BackendAvailabilities: dict[ExistingProcessBackendLabel, Union[bool, ImportError]] = {
    "Cython": CYTHON_AVAILABLE if CYTHON_AVAILABLE else FAILED_PYX_IMPORT,
    # "Rust": RUST_AVAILABLE if RUST_AVAILABLE else FAILED_RUST_IMPORT,
    "Python": True,
}
DEFAULT_PROCESS_BACKEND: ExistingProcessBackendLabel = (
    # "Rust" if RUST_AVAILABLE else ("Cython" if CYTHON_AVAILABLE else "Python")
    "Cython"
    if CYTHON_AVAILABLE
    else "Python"
)

# def echo_cell_rust(
#     idx: int,
#     first_counts: dict[str, int],
#     second_counts: dict[str, int],
#     bitstring_range: tuple[int, int],
#     subsystem_size: int,
# ) -> tuple[int, float]:
#     """Calculate the echo cell, one of overlap, of a subsystem by Rust.

#     Args:
#         idx (int): Index of the cell (counts).
#         first_counts (dict[str, int]): Counts measured by the first quantum circuit.
#         second_counts (dict[str, int]): Counts measured by the second quantum circuit.
#         bitstring_range (tuple[int, int]): The range of the subsystem.
#         subsystem_size (int): Subsystem size included.

#     Returns:
#         tuple[int, float]: Index, one of overlap purity.
#     """
#     return idx, purity_cell_rust_source(
#         dict(first_counts), dict(second_counts), bitstring_range, subsystem_size
#     )


def echo_cell_cy(
    idx: int,
    first_counts: dict[str, int],
    second_counts: dict[str, int],
    bitstring_range: tuple[int, int],
    subsystem_size: int,
) -> tuple[int, float]:
    """Calculate the echo cell, one of overlap, of a subsystem by Cython.

    Args:
        idx (int): Index of the cell (counts).
        first_counts (dict[str, int]): Counts measured by the first quantum circuit.
        second_counts (dict[str, int]): Counts measured by the second quantum circuit.
        bitstring_range (tuple[int, int]): The range of the subsystem.
        subsystem_size (int): Subsystem size included.

    Returns:
        tuple[int, float]: Index, one of overlap purity.
    """
    return idx, echoCellCore(
        dict(first_counts), dict(second_counts), bitstring_range, subsystem_size
    )


def echo_cell_py(
    idx: int,
    first_counts: dict[str, int],
    second_counts: dict[str, int],
    bitstring_range: tuple[int, int],
    subsystem_size: int,
) -> tuple[int, float]:
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

    _echo_cell = np.float64(0)
    for s_i, s_i_meas in first_counts_under_degree.items():
        for s_j, s_j_meas in second_counts_under_degree.items():
            _echo_cell += ensemble_cell_py(
                s_i, s_i_meas, s_j, s_j_meas, subsystem_size, shots
            )

    return idx, _echo_cell


def echo_cell(
    idx: int,
    first_counts: dict[str, int],
    second_counts: dict[str, int],
    bitstring_range: tuple[int, int],
    subsystem_size: int,
    backend: ExistingProcessBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[int, float]:
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
    # if not RUST_AVAILABLE and backend == "Rust":
    #     warnings.warn(
    #         "Rust is not available, using Cython or Python to calculate purity cell."
    #         + f"Check the error: {FAILED_RUST_IMPORT}",
    #         QurryRustUnavailableWarning,
    #     )
    #     backend = "Cython" if CYTHON_AVAILABLE else "Python"
    if not CYTHON_AVAILABLE and backend == "Cython":
        warnings.warn(
            "Cython is not available, using Python or Rust to calculate purity cell."
            + f"Check the error: {FAILED_PYX_IMPORT}",
            QurryCythonUnavailableWarning,
        )
        # backend = "Rust" if RUST_AVAILABLE else "Python"
        backend = "Python"

    if backend == "Cython":
        return echo_cell_cy(
            idx, first_counts, second_counts, bitstring_range, subsystem_size
        )
    # if backend == "Rust":
    #     return purity_cell_rust(idx, single_counts, bitstring_range, subsystem_size)
    return echo_cell_py(
        idx, first_counts, second_counts, bitstring_range, subsystem_size
    )
