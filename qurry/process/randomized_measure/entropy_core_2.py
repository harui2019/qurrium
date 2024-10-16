"""
================================================================
Postprocessing - Randomized Measure - Entangled Entropy Core 2
(:mod:`qurry.process.randomized_measure.entangled_core_2`)
================================================================

"""

import time
import warnings
from typing import Union, Optional
import numpy as np

from .purity_cell_2 import purity_cell_2_py
from ..utils import is_cycling_slice_active, degree_handler
from ..availability import (
    availablility,
    default_postprocessing_backend,
    PostProcessingBackendLabel,
)
from ..exceptions import (
    # PostProcessingRustImportError,
    PostProcessingRustUnavailableWarning,
    # PostProcessingBackendDeprecatedWarning,
)
from ...tools import ParallelManager, workers_distribution


# try:
#     from ...boorust import randomized  # type: ignore

#     entangled_entropy_core_rust_source = randomized.entangled_entropy_core_rust

#     RUST_AVAILABLE = True
#     FAILED_RUST_IMPORT = None
# except ImportError as err:
#     RUST_AVAILABLE = False
#     FAILED_RUST_IMPORT = err

#     def entangled_entropy_core_rust_source(*args, **kwargs):
#         """Dummy function for entangled_entropy_core_rust."""
#         raise PostProcessingRustImportError(
#             "Rust is not available, using python to calculate entangled entropy."
#         ) from FAILED_RUST_IMPORT

RUST_AVAILABLE = False
FAILED_RUST_IMPORT = None

BACKEND_AVAILABLE = availablility(
    "randomized_measure.entangled_core_2",
    [
        ("Rust", RUST_AVAILABLE, FAILED_RUST_IMPORT),
    ],
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(RUST_AVAILABLE, False)


def entangled_entropy_core_2_pyrust(
    shots: int,
    counts: list[dict[str, int]],
    degree_or_selected: Optional[Union[tuple[int, int], int, list[int]]],
    backend: PostProcessingBackendLabel = "Rust",
) -> tuple[
    dict[int, np.float64],
    list[int],
    str,
    float,
]:
    """The core function of entangled entropy by Python or Rust for just purity cell part.

    Args:
        shots (int):
            Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        degree_or_selected (Optional[Union[tuple[int, int], int, list[int]]]):
            The list of the selected qubits or the degree of the subsystem.
        backend (ExistingProcessBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.

    Raises:
        ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
        ValueError: Measure range does not contain subsystem.

    Returns:
        tuple[dict[int, np.float64], list[int], str, float]:
            Purity of each cell, Selected qubits, Message, Time to calculate.
    """

    # check shots
    sample_shots = sum(counts[0].values())
    assert sample_shots == shots, f"shots {shots} does not match sample_shots {sample_shots}"

    # Determine worker number
    launch_worker = workers_distribution()

    # Determine subsystem size
    allsystem_size = len(list(counts[0].keys())[0])

    # Determine degree
    if isinstance(degree_or_selected, (int, tuple)) or degree_or_selected is None:
        bitstring_range, measure, subsystem_size = degree_handler(
            allsystem_size, degree_or_selected, None
        )

        msg = (
            "| Partition: "
            + (
                "cycling-"
                if is_cycling_slice_active(allsystem_size, bitstring_range, subsystem_size)
                else ""
            )
            + f"{bitstring_range}, Measure: {measure}, backend: {backend}"
        )
        selected_qubits = list(range(allsystem_size))
        selected_qubits = sorted(selected_qubits, reverse=True)[
            bitstring_range[0] : bitstring_range[1]
        ]

    elif isinstance(degree_or_selected, list):
        selected_qubits = degree_or_selected
        assert all(
            0 <= q_i < allsystem_size for q_i in selected_qubits
        ), f"Invalid selected qubits: {selected_qubits}"
        msg = f"| Selected qubits: {selected_qubits}"

    else:
        raise ValueError(f"Invalid degree_or_selected: {degree_or_selected}")

    begin = time.time()

    cell_calculation = purity_cell_2_py
    if backend != "Python":
        warnings.warn(
            "The Rust is not implemented yet, using Python to calculate purity cell.",
            PostProcessingRustUnavailableWarning,
        )

    pool = ParallelManager(launch_worker)
    purity_cell_result_list = pool.starmap(
        cell_calculation,
        [(i, c, selected_qubits) for i, c in enumerate(counts)],
    )
    taken = round(time.time() - begin, 3)

    selected_qubits_sorted = sorted(selected_qubits, reverse=True)

    purity_cell_dict: dict[int, np.float64] = {}
    selected_qubits_checked: dict[int, bool] = {}
    for idx, purity_cell_value, selected_qubits_sorted_result in purity_cell_result_list:
        purity_cell_dict[idx] = purity_cell_value
        if selected_qubits_sorted_result != selected_qubits_sorted:
            selected_qubits_checked[idx] = False

    if len(selected_qubits_checked) > 0:
        warnings.warn(
            f"Selected qubits are not sorted for {len(selected_qubits_checked)} cells.",
            RuntimeWarning,
        )

    return purity_cell_dict, selected_qubits_sorted, msg, taken


def entangled_entropy_core_2(
    shots: int,
    counts: list[dict[str, int]],
    degree_or_selected: Optional[Union[tuple[int, int], int, list[int]]],
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[
    dict[int, np.float64],
    list[int],
    str,
    float,
]:
    """The core function of entangled entropy.

    Args:
        shots (int):
            Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        degree_or_selected (Optional[Union[tuple[int, int], int, list[int]]]):
            The list of the selected qubits or the degree of the subsystem.
        backend (ExistingProcessBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.

    Raises:
        ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
        ValueError: Measure range does not contain subsystem.

    Returns:
        tuple[dict[int, np.float64], list[int], str, float]:
            Purity of each cell, Selected qubits, Message, Time to calculate.
    """

    return entangled_entropy_core_2_pyrust(shots, counts, degree_or_selected, backend)
