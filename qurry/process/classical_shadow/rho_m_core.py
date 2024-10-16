"""
================================================================
Postprocessing - Classical Shadow - Rho M Core
(:mod:`qurry.process.classical_shadow.rho_m_core`)
================================================================

"""

import time
import warnings
from typing import Literal, Union
import numpy as np

from .rho_m_cell import rho_m_cell_py
from ..utils import is_cycling_slice_active, degree_handler
from ..availability import (
    availablility,
    default_postprocessing_backend,
    # PostProcessingBackendLabel,
)
from ...tools import ParallelManager, workers_distribution


RUST_AVAILABLE = False
FAILED_RUST_IMPORT = None

BACKEND_AVAILABLE = availablility(
    "randomized_measure.entangled_core_2",
    [
        ("Rust", RUST_AVAILABLE, FAILED_RUST_IMPORT),
        ("Cython", "Depr.", None),
    ],
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(RUST_AVAILABLE, False)


def rho_m_core_py(
    shots: int,
    counts: list[dict[str, int]],
    random_unitary_um: dict[int, dict[int, Union[Literal[0, 1, 2], int]]],
    degree_or_selected: Union[tuple[int, int], int, list[int]],
) -> tuple[
    dict[int, np.ndarray[tuple[int, int], np.dtype[np.complex128]]],
    dict[int, dict[int, np.ndarray[tuple[Literal[2], Literal[2]], np.dtype[np.complex128]]]],
    list[int],
    str,
    float,
]:
    """Rho M Core calculation.

    Args:
        shots (int):
            The number of shots.
        counts (list[dict[str, int]]):
            The list of the counts.
        random_unitary_um (dict[int, dict[int, Union[Literal[0, 1, 2], int]]]):
            The shadow direction of the unitary operators.
        degree_or_selected (Union[tuple[int, int], int, list[int]]):
            The degree or the selected qubits.

    Returns:
        tuple[
            dict[int, np.ndarray[tuple[int, int], np.dtype[np.complex128]]],
            dict[int, dict[
                int, np.ndarray[tuple[Literal[2], Literal[2]], np.dtype[np.complex128]]
            ]],
            list[int],
            str,
            float
        ]:
            The rho_m, the set of rho_m_i,
            the sorted list of the selected qubits,
            the message, the taken time.
    """
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
            + f"{bitstring_range}, Measure: {measure}"
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

    pool = ParallelManager(launch_worker)
    rho_m_py_result_list = pool.starmap(
        rho_m_cell_py,
        [
            (idx, single_counts, random_unitary_um[idx], selected_qubits)
            for idx, single_counts in enumerate(counts)
        ],
    )

    taken = round(time.time() - begin, 3)

    selected_qubits_sorted = sorted(selected_qubits, reverse=True)

    rho_m_dict: dict[int, np.ndarray[tuple[int, int], np.dtype[np.complex128]]] = {}
    rho_m_i_dict: dict[
        int, dict[int, np.ndarray[tuple[Literal[2], Literal[2]], np.dtype[np.complex128]]]
    ] = {}
    selected_qubits_checked: dict[int, bool] = {}
    for idx, rho_m, rho_m_i, selected_qubits_sorted_result in rho_m_py_result_list:
        rho_m_dict[idx] = rho_m
        rho_m_i_dict[idx] = rho_m_i
        if selected_qubits_sorted_result != selected_qubits_sorted:
            selected_qubits_checked[idx] = False

    if len(selected_qubits_checked) > 0:
        warnings.warn(
            f"Selected qubits are not sorted for {len(selected_qubits_checked)} cells.",
            RuntimeWarning,
        )

    return rho_m_dict, rho_m_i_dict, selected_qubits_sorted, msg, taken
