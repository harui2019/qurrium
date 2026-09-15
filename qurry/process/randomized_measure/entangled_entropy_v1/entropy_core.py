"""Post Processing - Randomized Measure - Entangled Entropy V1 - Core
(:mod:`qurry.process.randomized_measure.entangled_entropy_v1.entropy_core`)

"""

import time
import warnings
import numpy as np

from .purity_cell import purity_cell_py
from ...utils import is_cycling_slice_active, degree_handler
from ...availability import (
    availability,
    default_postprocessing_backend,
    PostProcessingBackendLabel,
)
from ...exceptions import PostProcessingBackendDeprecatedWarning
from ....tools import ParallelManager, workers_distribution

# pylint: disable=import-error,no-name-in-module
from ....boorust.randomized import entangled_entropy_core_rust  # type: ignore


BACKEND_AVAILABLE = availability(
    "randomized_measure.entangled_entropy_v1.entropy_core",
    [("Rust", True, None), ("Cython", "Depr.", None)],
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(True, False)


def entangled_entropy_core_py(
    shots: int,
    counts: list[dict[str, int]],
    degree: tuple[int, int] | int | None,
    measure: tuple[int, int] | None = None,
    multiprocess_pool_size: int | None = None,
) -> tuple[dict[int, float] | dict[int, np.float64], tuple[int, int], tuple[int, int], str, float]:
    """The core function of entangled entropy by Python for just purity cell part.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (tuple[int, int] | int | None): Degree of the subsystem.
        measure (tuple[int, int] | None, optional):
            Measuring range on quantum circuits. Defaults to None.
        multiprocess_pool_size(int | None, optional):
            Number of multi-processing workers,
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts by `os.cpu_count()`.
            Defaults to None.

    Raises:
        ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
        ValueError: Measure range does not contain subsystem.

    Returns:
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
    bitstring_range, measure, subsystem_size = degree_handler(allsystem_size, degree, measure)

    msg = (
        "| Partition: "
        + (
            "cycling-"
            if is_cycling_slice_active(allsystem_size, bitstring_range, subsystem_size)
            else ""
        )
        + f"{bitstring_range}, Measure: {measure}, backend: Python"
    )

    times = len(counts)
    begin = time.time()

    msg += (
        f", single process, {times} overlaps, it will take a lot of time."
        if launch_worker == 1
        else f", {launch_worker} workers, {times} overlaps."
    )

    pm = ParallelManager(launch_worker)
    purity_cell_items = pm.starmap(
        purity_cell_py,
        [(i, c, bitstring_range, subsystem_size) for i, c in enumerate(counts)],
    )

    taken = round(time.time() - begin, 3)
    purity_cell_dict: dict[int, float] | dict[int, np.float64] = dict(purity_cell_items)
    return purity_cell_dict, bitstring_range, measure, msg, taken


def entangled_entropy_core(
    shots: int,
    counts: list[dict[str, int]],
    degree: tuple[int, int] | int | None,
    measure: tuple[int, int] | None = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    multiprocess_pool_size: int | None = None,
) -> tuple[dict[int, float] | dict[int, np.float64], tuple[int, int], tuple[int, int], str, float]:
    """The core function of entangled entropy.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (tuple[int, int] | int | None): Degree of the subsystem.
        measure (tuple[int, int] | None, optional):
            Measuring range on quantum circuits. Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
        multiprocess_pool_size(int | None, optional):
            Number of multi-processing workers, it will be ignored if backend is Rust.
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts by `os.cpu_count()`.
            Defaults to None.

    Raises:
        ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
        ValueError: Measure range does not contain subsystem.

    Returns:
        Purity of each cell, Partition range, Measuring range, Message, Time to calculate.
    """

    if isinstance(measure, list):
        measure = tuple(measure)  # type: ignore
    assert isinstance(measure, tuple) or measure is None, f"measure {measure} is not tuple or None."

    if backend == "Cython":
        warnings.warn(
            "Cython backend is deprecated, using Python or Rust to calculate purity cell.",
            PostProcessingBackendDeprecatedWarning,
        )
        backend = DEFAULT_PROCESS_BACKEND
    if backend == "Rust":
        return entangled_entropy_core_rust(shots, counts, degree, measure)

    return entangled_entropy_core_py(shots, counts, degree, measure, multiprocess_pool_size)
