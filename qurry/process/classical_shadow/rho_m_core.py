"""
================================================================
Postprocessing - Classical Shadow - Rho M Core
(:mod:`qurry.process.classical_shadow.rho_m_core`)
================================================================

"""

import time
from typing import Literal, Union, Optional
import numpy as np

from .rho_m_cell import rho_m_cell_py
from ..utils import cycling_slice as cycling_slice_py, qubit_selector
from ..availability import (
    availablility,
    default_postprocessing_backend,
    PostProcessingBackendLabel,
)
from ...tools import ParallelManager, workers_distribution


RUST_AVAILABLE = False
FAILED_RUST_IMPORT = None

BACKEND_AVAILABLE = availablility(
    "randomized_measure.entangled_core",
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
    degree_or_selected: Optional[Union[tuple[int, int], int, list[int]]],
):
    sample_shots = sum(counts[0].values())
    assert sample_shots == shots, f"shots {shots} does not match sample_shots {sample_shots}"

    # Determine worker number
    launch_worker = workers_distribution()

    # Determine subsystem size
    allsystem_size = len(list(counts[0].keys())[0])

    # Determine degree
    if isinstance(degree_or_selected, (int, tuple)):
        degree = qubit_selector(allsystem_size, degree=degree_or_selected)
        subsystem_size = max(degree) - min(degree)

        bitstring_range = degree
        bitstring_check = {
            "b > a": (bitstring_range[1] > bitstring_range[0]),
            "a >= -allsystemSize": bitstring_range[0] >= -allsystem_size,
            "b <= allsystemSize": bitstring_range[1] <= allsystem_size,
            "b-a <= allsystemSize": ((bitstring_range[1] - bitstring_range[0]) <= allsystem_size),
        }
        if not all(bitstring_check.values()):
            raise ValueError(
                f"Invalid 'bitStringRange = {bitstring_range} "
                + f"for allsystemSize = {allsystem_size}'. "
                + "Available range 'bitStringRange = [a, b)' should be"
                + ", ".join([f" {k};" for k, v in bitstring_check.items() if not v])
            )

        _dummy_string = "".join(str(ds) for ds in range(allsystem_size))
        _dummy_string_slice = cycling_slice_py(
            _dummy_string, bitstring_range[0], bitstring_range[1], 1
        )
        is_avtive_cycling_slice = (
            _dummy_string[bitstring_range[0] : bitstring_range[1]] != _dummy_string_slice
        )
        if is_avtive_cycling_slice:
            assert len(_dummy_string_slice) == subsystem_size, (
                f"| All system size '{subsystem_size}' "
                + f"does not match dummyStringSlice '{_dummy_string_slice}'"
            )

        msg = (
            "| Partition: " + ("cycling-" if is_avtive_cycling_slice else "") + f"{bitstring_range}"
        )

        selected_qubits = list(range(bitstring_range[0], bitstring_range[1]))
    elif isinstance(degree_or_selected, list):
        selected_qubits = degree_or_selected
        assert all(
            [0 <= q_i < allsystem_size for q_i in selected_qubits]
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

    rho_m_dict = {}
    rho_m_i_dict = {}
    selected_qubits_dict = {}
    for idx, rho_m, rho_m_i, selected_qubits_sorted in rho_m_py_result_list:
        rho_m_dict[idx] = rho_m
        rho_m_i_dict[idx] = rho_m_i
        selected_qubits_dict[idx] = selected_qubits_sorted

    return rho_m_dict, rho_m_i_dict, selected_qubits_dict, msg, taken
