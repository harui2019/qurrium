"""
=========================================================================================
Postprocessing - Randomized Measure - Wavefunction Overlap - Echo Core
(:mod:`qurry.process.randomized_measure.wavefunction_overlap.echo_core`)
=========================================================================================

"""

import time
import warnings
from typing import Union, Optional
import numpy as np

from .echo_cell import echo_cell_py, echo_cell_rust
from ...utils import cycling_slice as cycling_slice_py, qubit_selector
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
from ....tools import ParallelManager, workers_distribution

try:
    from ....boorust import randomized  # type: ignore

    overlap_echo_core_rust_source = randomized.overlap_echo_core_rust

    RUST_AVAILABLE = True
    FAILED_RUST_IMPORT = None
except ImportError as err:
    RUST_AVAILABLE = False
    FAILED_RUST_IMPORT = err

    def overlap_echo_core_rust_source(*args, **kwargs):
        """Dummy function for entangled_entropy_core_rust."""
        raise PostProcessingRustImportError(
            "Rust is not available, using python to calculate overlap echo."
        ) from FAILED_RUST_IMPORT


BACKEND_AVAILABLE = availablility(
    "randomized_measure.wavefunction_overlap",
    [
        ("Rust", RUST_AVAILABLE, FAILED_RUST_IMPORT),
        ("Cython", "Depr.", None),
    ],
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(
    RUST_AVAILABLE,
    False,
)


def overlap_echo_core_pycyrust(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]] = None,
    measure: Optional[tuple[int, int]] = None,
    multiprocess_pool_size: Optional[int] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[
    Union[dict[int, float], dict[int, np.float64]],
    tuple[int, int],
    tuple[int, int],
    str,
    float,
]:
    """The core function of entangled entropy.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (Union[tuple[int, int], int]): Degree of the subsystem.
        measure (tuple[int, int], optional): Measuring range on quantum circuits. Defaults to None.
        multiprocess_pool_size(Optional[int], optional):
            Number of multi-processing workers,
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts by `os.cpu_count()`.
            Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            Backend for the process. Defaults to 'Cython'.

    Raises:
        ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
        ValueError: Measure range does not contain subsystem.

    Returns:
        tuple[
            Union[dict[int, float], dict[int, np.float64]],
            tuple[int, int],
            tuple[int, int],
            str,
            float
        ]:
            Purity of each cell, Partition range, Measuring range, Message, Time to calculate.
    """

    # check shots
    sample_shots = sum(counts[0].values())
    assert sample_shots == shots, f"shots {shots} does not match sample_shots {sample_shots}"

    # Determine worker number
    launch_worker = workers_distribution(multiprocess_pool_size)

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

    _dummy_string = list(range(allsystem_size))
    _dummy_string_slice = cycling_slice_py(_dummy_string, bitstring_range[0], bitstring_range[1], 1)
    is_avtive_cycling_slice = (
        _dummy_string[bitstring_range[0] : bitstring_range[1]] != _dummy_string_slice
    )
    if is_avtive_cycling_slice:
        assert len(_dummy_string_slice) == subsystem_size, (
            f"| All system size '{subsystem_size}' "
            + f"does not match dummyStringSlice '{_dummy_string_slice}'"
        )

    times = len(counts) / 2
    assert times == int(times), f"counts {len(counts)} is not even."
    times = int(times)
    counts_pair = list(zip(counts[:times], counts[times:]))

    begin_time = time.time()

    msg = f"| Partition: {bitstring_range}, Measure: {measure}"

    if backend not in BACKEND_AVAILABLE[1]:
        warnings.warn(
            f"Unknown backend '{backend}', using {DEFAULT_PROCESS_BACKEND} instead.",
        )
        backend = DEFAULT_PROCESS_BACKEND

    if not RUST_AVAILABLE and backend == "Rust":
        warnings.warn(
            "Rust is not available, using Python to calculate purity cell."
            + f"Check the error: {FAILED_RUST_IMPORT}",
            PostProcessingRustUnavailableWarning,
        )
        backend = "Python"

    cell_calculation = echo_cell_rust if backend == "Rust" else echo_cell_py

    if launch_worker == 1:
        echo_cell_items = []
        msg += f", single process, {times} overlaps, it will take a lot of time."
        print(msg)
        for i, (c1, c2) in enumerate(counts_pair):
            echo_cell_items.append(cell_calculation(i, c1, c2, bitstring_range, subsystem_size))

        take_time = round(time.time() - begin_time, 3)
    else:
        msg += f", {launch_worker} workers, {times} overlaps."

        pool = ParallelManager(launch_worker)
        echo_cell_items = pool.starmap(
            cell_calculation,
            [
                (i, c1, c2, bitstring_range, subsystem_size)
                for i, (c1, c2) in enumerate(counts_pair)
            ],
        )
        take_time = round(time.time() - begin_time, 3)

    echo_cell_dict: Union[dict[int, float], dict[int, np.float64]] = dict(
        echo_cell_items
    )  # type: ignore
    return echo_cell_dict, bitstring_range, measure, msg, take_time


def overlap_echo_allrust(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Optional[tuple[int, int]] = None,
) -> tuple[dict[int, float], tuple[int, int], tuple[int, int], str, float]:
    """The core function of entangled entropy.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (Optional[Union[tuple[int, int], int]]): Degree of the subsystem.
        measure (Optional[tuple[int, int]], optional):
            Measuring range on quantum circuits. Defaults to None.

    Raises:
        ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
        ValueError: Measure range does not contain subsystem.

    Returns:
        tuple[dict[int, float], tuple[int, int], tuple[int, int], str, float]:
            Purity of each cell, Partition range, Measuring range, Message, Time to calculate.
    """

    return overlap_echo_core_rust_source(shots, counts, degree, measure)


def overlap_echo_core(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Optional[tuple[int, int]] = None,
    multiprocess_pool_size: Optional[int] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[
    Union[dict[int, float], dict[int, np.float64]],
    tuple[int, int],
    tuple[int, int],
    str,
    float,
]:
    """The core function of entangled entropy.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (Union[tuple[int, int], int]): Degree of the subsystem.
        measure (tuple[int, int], optional): Measuring range on quantum circuits. Defaults to None.
        workers_num (Optional[int], optional):
            Number of multi-processing workers,
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts - 2 by `cpu_count() - 2`.
            Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            The backend of the process, 'Cython', 'Rust' or 'Python'.
            Defaults to DEFAULT_PROCESS_BACKEND.

    Raises:
        ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
        ValueError: Measure range does not contain subsystem.

    Returns:
        tuple[
            Union[dict[int, float], dict[int, np.float64]],
            tuple[int, int],
            tuple[int, int],
            str,
            float,
        ]:
            Purity of each cell, Partition range, Measuring range, Message, Time to calculate.
    """

    if isinstance(measure, list):
        measure = tuple(measure)  # type: ignore

    if backend == "Cython":
        warnings.warn(
            "Cython backend is deprecated, using Python or Rust to calculate purity cell.",
            PostProcessingBackendDeprecatedWarning,
        )
        backend = DEFAULT_PROCESS_BACKEND
    if backend == "Rust":
        if RUST_AVAILABLE:
            return overlap_echo_allrust(shots, counts, degree, measure)
        backend = "Python"
        warnings.warn(
            f"Rust is not available, using {backend} to calculate purity cell."
            + f" Check the error: {FAILED_RUST_IMPORT}",
            PostProcessingRustUnavailableWarning,
        )

    return overlap_echo_core_pycyrust(
        shots, counts, degree, measure, multiprocess_pool_size, backend
    )
