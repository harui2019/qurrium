"""
================================================================
Postprocessing - Classical Shadow - Purity Core
(:mod:`qurry.process.classical_shadow.purity_core`)
================================================================

"""

import time
from typing import Literal, Union, Optional
import numpy as np

from .rho_m_cell import rho_m_py
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


def rho_m_core_pyrust(
    shots: int,
    counts: list[dict[str, int]],
    degree_or_selected: Optional[Union[tuple[int, int], int, list[int]]],
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
):
    sample_shots = sum(counts[0].values())
    assert sample_shots == shots, f"shots {shots} does not match sample_shots {sample_shots}"

    # Determine worker number
    launch_worker = workers_distribution()

    # Determine subsystem size
    allsystem_size = len(list(counts[0].keys())[0])

    # Determine degree
    degree = qubit_selector(allsystem_size, degree=degree)
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
            f"Invalid 'bitStringRange = {bitstring_range} for allsystemSize = {allsystem_size}'. "
            + "Available range 'bitStringRange = [a, b)' should be"
            + ", ".join([f" {k};" for k, v in bitstring_check.items() if not v])
        )

    if measure is None:
        measure = qubit_selector(len(list(counts[0].keys())[0]))

    _dummy_string = "".join(str(ds) for ds in range(allsystem_size))
    _dummy_string_slice = cycling_slice_py(_dummy_string, bitstring_range[0], bitstring_range[1], 1)
    is_avtive_cycling_slice = (
        _dummy_string[bitstring_range[0] : bitstring_range[1]] != _dummy_string_slice
    )
    if is_avtive_cycling_slice:
        assert len(_dummy_string_slice) == subsystem_size, (
            f"| All system size '{subsystem_size}' "
            + f"does not match dummyStringSlice '{_dummy_string_slice}'"
        )

    msg = (
        "| Partition: "
        + ("cycling-" if is_avtive_cycling_slice else "")
        + f"{bitstring_range}, Measure: {measure}, backend: {backend}"
    )

    times = len(counts)
    begin = time.time()

    pool = ParallelManager(launch_worker)
    rho_ms = pool.starmap(
        rho_m_py,
        [
            (idx, single_counts, bitstring_range, subsystem_size)
            for idx, single_counts in enumerate(counts)
        ],
    )

    taken = round(time.time() - begin, 3)