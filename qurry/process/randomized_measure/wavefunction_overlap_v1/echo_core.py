"""Post Processing - Randomized Measure - Wavefunction Overlap V1 - Echo Core
(:mod:`qurry.process.randomized_measure.wavefunction_overlap_v1.echo_core`)

"""

import time
import warnings
import numpy as np

from .echo_cell import echo_cell_py
from ...utils import cycling_slice as cycling_slice_py, qubit_selector
from ...availability import (
    availability,
    default_postprocessing_backend,
    PostProcessingBackendLabel,
)
from ...exceptions import PostProcessingBackendDeprecatedWarning
from ....tools import ParallelManager, workers_distribution

# pylint: disable=import-error,no-name-in-module
from ....boorust.randomized import overlap_echo_core_rust  # type: ignore


BACKEND_AVAILABLE = availability(
    "randomized_measure.wavefunction_overlap_v1.echo_core",
    [("Rust", True, None), ("Cython", "Depr.", None)],
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(True, False)


def overlap_echo_core_py(
    shots: int,
    counts: list[dict[str, int]],
    degree: tuple[int, int] | int | None = None,
    measure: tuple[int, int] | None = None,
    multiprocess_pool_size: int | None = None,
) -> tuple[dict[int, float] | dict[int, np.float64], tuple[int, int], tuple[int, int], str, float]:
    """The core function of entangled entropy.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (tuple[int, int] | int | None, optional): Degree of the subsystem.
        measure (tuple[int, int] | None, optional):
            Measuring range on quantum circuits. Defaults to None.
        multiprocess_pool_size(int | None, optional):
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
        Echo of each cell, Partition range, Measuring range, Message, Time to calculate.
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

    msg += (
        f", single process, {times} overlaps, it will take a lot of time."
        if launch_worker == 1
        else f", {launch_worker} workers, {times} overlaps."
    )
    pm = ParallelManager(launch_worker)
    echo_cell_items = pm.starmap(
        echo_cell_py,
        [(i, c1, c2, bitstring_range, subsystem_size) for i, (c1, c2) in enumerate(counts_pair)],
    )
    take_time = round(time.time() - begin_time, 3)

    echo_cell_dict: dict[int, float] | dict[int, np.float64] = dict(echo_cell_items)
    return echo_cell_dict, bitstring_range, measure, msg, take_time


def overlap_echo_core(
    shots: int,
    counts: list[dict[str, int]],
    degree: tuple[int, int] | int | None,
    measure: tuple[int, int] | None = None,
    multiprocess_pool_size: int | None = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[dict[int, float] | dict[int, np.float64], tuple[int, int], tuple[int, int], str, float]:
    """The core function of entangled entropy.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (tuple[int, int] | int | None, optional): Degree of the subsystem.
        measure (tuple[int, int] | None, optional):
            Measuring range on quantum circuits. Defaults to None.
        multiprocess_pool_size (int | None, optional):
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
        Echo of each cell, Partition range, Measuring range, Message, Time to calculate.
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
        return overlap_echo_core_rust(shots, counts, degree, measure)

    return overlap_echo_core_py(shots, counts, degree, measure, multiprocess_pool_size)
