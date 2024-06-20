"""
================================================================
Postprocessing - Randomized Measure - Entangled Entropy Core
(:mod:`qurry.process.randomized_measure.entangled_core`)
================================================================

"""

import time
import warnings
from typing import Union, Optional
import numpy as np

from .purity_cell import (
    purity_cell_py,
    purity_cell_cy,
    purity_cell_rust,
    CYTHON_AVAILABLE,
    FAILED_PYX_IMPORT,
)
from ..utils import cycling_slice as cycling_slice_py, qubit_selector
from ..availability import (
    availablility,
    default_postprocessing_backend,
    PostProcessingBackendLabel,
)
from ..exceptions import (
    PostProcessingCythonUnavailableWarning,
    PostProcessingRustImportError,
    PostProcessingRustUnavailableWarning,
)
from ...tools import ParallelManager, workers_distribution


try:
    from ...boorust import randomized  # type: ignore

    entangled_entropy_core_rust_source = randomized.entangled_entropy_core_rust

    RUST_AVAILABLE = True
    FAILED_RUST_IMPORT = None
except ImportError as err:
    RUST_AVAILABLE = False
    FAILED_RUST_IMPORT = err

    def entangled_entropy_core_rust_source(*args, **kwargs):
        """Dummy function for entangled_entropy_core_rust."""
        raise PostProcessingRustImportError(
            "Rust is not available, using python to calculate entangled entropy."
        ) from FAILED_RUST_IMPORT


BACKEND_AVAILABLE = availablility(
    "randomized_measure.entangled_core",
    [
        ("Rust", RUST_AVAILABLE, FAILED_RUST_IMPORT),
        ("Cython", CYTHON_AVAILABLE, FAILED_PYX_IMPORT),
    ],
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(RUST_AVAILABLE, CYTHON_AVAILABLE)


def entangled_entropy_core_pycyrust(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Optional[tuple[int, int]] = None,
    multiprocess_pool_size: Optional[int] = None,
    backend: PostProcessingBackendLabel = "Cython",
) -> tuple[
    Union[dict[int, float], dict[int, np.float64]],
    tuple[int, int],
    tuple[int, int],
    str,
    float,
]:
    """The core function of entangled entropy by Cython, Python, or Rust for just purity cell part.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (Optional[Union[tuple[int, int], int]]): Degree of the subsystem.
        measure (Optional[tuple[int, int]], optional):
            Measuring range on quantum circuits. Defaults to None.
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
            float,
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

    if backend not in BACKEND_AVAILABLE[1]:
        warnings.warn(
            f"Unknown backend '{backend}', using {DEFAULT_PROCESS_BACKEND} instead.",
        )
        backend = DEFAULT_PROCESS_BACKEND

    if not RUST_AVAILABLE and backend == "Rust":
        warnings.warn(
            "Rust is not available, using Cython or Python to calculate purity cell."
            + f"Check the error: {FAILED_RUST_IMPORT}",
            PostProcessingRustUnavailableWarning,
        )
        backend = "Cython" if CYTHON_AVAILABLE else "Python"
    if not CYTHON_AVAILABLE and backend == "Cython":
        warnings.warn(
            "Cython is not available, using Python to calculate purity cell."
            + f"Check the error: {FAILED_PYX_IMPORT}",
            PostProcessingCythonUnavailableWarning,
        )
        backend = "Rust" if RUST_AVAILABLE else "Python"

    cell_calculation = (
        purity_cell_cy
        if backend == "Cython"
        else (purity_cell_rust if backend == "Rust" else purity_cell_py)
    )

    msg = (
        "| Partition: "
        + ("cycling-" if is_avtive_cycling_slice else "")
        + f"{bitstring_range}, Measure: {measure}, backend: {backend}"
    )

    times = len(counts)
    begin = time.time()

    if launch_worker == 1:
        purity_cell_items = []
        msg += f", single process, {times} overlaps, it will take a lot of time."
        print(msg)
        for i, c in enumerate(counts):
            purity_cell_items.append(cell_calculation(i, c, bitstring_range, subsystem_size))

    else:
        msg += f", {launch_worker} workers, {times} overlaps."

        pool = ParallelManager(launch_worker)
        purity_cell_items = pool.starmap(
            cell_calculation,
            [(i, c, bitstring_range, subsystem_size) for i, c in enumerate(counts)],
        )

    taken = round(time.time() - begin, 3)
    purity_cell_dict: Union[dict[int, float], dict[int, np.float64]] = dict(
        purity_cell_items
    )  # type: ignore
    return purity_cell_dict, bitstring_range, measure, msg, taken


def entangled_entropy_core_allrust(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Optional[tuple[int, int]] = None,
) -> tuple[dict[int, float], tuple[int, int], tuple[int, int], str, float,]:
    """The core function of entangled entropy by Rust.

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

    return entangled_entropy_core_rust_source(shots, counts, degree, measure)


def entangled_entropy_core(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Union[tuple[int, int], list[int], None] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    multiprocess_pool_size: Optional[int] = None,
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
        degree (Optional[Union[tuple[int, int], int]]): Degree of the subsystem.
        measure (Optional[tuple[int, int]], optional):
            Measuring range on quantum circuits. Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
        multiprocess_pool_size(Optional[int], optional):
            Number of multi-processing workers, it will be ignored if backend is Rust.
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts by `os.cpu_count()`.
            Defaults to None.

    Raises:
        ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
        ValueError: Measure range does not contain subsystem.

    Returns:
        tuple[dict[int, float], tuple[int, int], tuple[int, int], str, float]:
            Purity of each cell, Partition range, Measuring range, Message, Time to calculate.
    """

    if isinstance(measure, list):
        measure = tuple(measure)  # type: ignore
    assert isinstance(measure, tuple) or measure is None, f"measure {measure} is not tuple or None."

    if backend == "Rust":
        if RUST_AVAILABLE:
            return entangled_entropy_core_allrust(shots, counts, degree, measure)
        backend = "Cython" if CYTHON_AVAILABLE else "Python"
        warnings.warn(
            f"Rust is not available, using {backend} to calculate purity cell."
            + f" Check the error: {FAILED_RUST_IMPORT}",
            PostProcessingRustUnavailableWarning,
        )

    return entangled_entropy_core_pycyrust(
        shots, counts, degree, measure, multiprocess_pool_size, backend
    )
