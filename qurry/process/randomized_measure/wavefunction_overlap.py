"""
================================================================
Postprocessing - Randomized Measure - Wavefunction Overlap
(:mod:`qurry.process.randomized_measure.wavefunction_overlap`)
================================================================

"""

import time
import warnings
from typing import Union, Optional
import numpy as np
import tqdm

from .echo_cell import (
    echo_cell_py,
    echo_cell_cy,
    # echo_cell_rust,
    CYTHON_AVAILABLE,
    FAILED_PYX_IMPORT,
)
from ..utils import qubit_selector
from ..availability import (
    availablility,
    default_postprocessing_backend,
    PostProcessingBackendLabel,
)
from ..exceptions import (
    PostProcessingCythonUnavailableWarning,
    # PostProcessingRustImportError,
    # PostProcessingRustUnavailableWarning,
)
from ...tools import (
    ParallelManager,
    workers_distribution,
)

# try:
#     from ..boorust import randomized  # type: ignore

#     overlap_echo_core_rust_source = randomized.overlap_echo_core

#     RUST_AVAILABLE = True
#     FAILED_RUST_IMPORT = None
# except ImportError as err:
#     RUST_AVAILABLE = False
#     FAILED_RUST_IMPORT = err

#     def overlap_echo_core_rust_source(*args, **kwargs):
#         """Dummy function for entangled_entropy_core_rust."""
#         raise PostProcessingRustImportError(
#             "Rust is not available, using python to calculate overlap echo."
#         ) from FAILED_RUST_IMPORT

PostProcessingBackendStatement = availablility(
    "randomized_measure.entangled_entropy",
    [
        # ("Rust", RUST_AVAILABLE, FAILED_RUST_IMPORT),
        ("Cython", CYTHON_AVAILABLE, FAILED_PYX_IMPORT),
    ],
)
DEFAULT_PROCESS_BACKEND = default_postprocessing_backend(
    # RUST_AVAILABLE,
    False,
    CYTHON_AVAILABLE,
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
            float
        ]:
            Purity of each cell, Partition range, Measuring range, Message, Time to calculate.
    """

    # check shots
    sample_shots = sum(counts[0].values())
    assert (
        sample_shots == shots
    ), f"shots {shots} does not match sample_shots {sample_shots}"

    # Determine worker number
    launch_worker = workers_distribution(multiprocess_pool_size)

    # Determine degree
    if degree is None:
        degree = qubit_selector(len(list(counts[0].keys())[0]))

    # Determine subsystem size
    if isinstance(degree, int):
        subsystem_size = degree
        degree = qubit_selector(len(list(counts[0].keys())[0]), degree=degree)

    elif isinstance(degree, (tuple, list)):
        subsystem_size = max(degree) - min(degree)

    else:
        raise ValueError(
            f"'degree' must be 'int' or 'tuple[int, int]', but get '{degree}'."
        )

    if measure is None:
        measure = qubit_selector(len(list(counts[0].keys())[0]))

    if (min(degree) < min(measure)) or (max(degree) > max(measure)):
        raise ValueError(
            f"Measure range '{measure}' does not contain subsystem '{degree}'."
        )

    bitstring_range = (min(degree) - min(measure), max(degree) - min(measure))
    print(
        f"| Subsystem size: {subsystem_size}, bitstring range: "
        + f"{bitstring_range}, measure range: {measure}."
    )

    times = len(counts) / 2
    assert times == int(times), f"counts {len(counts)} is not even."
    times = int(times)
    counts_pair = list(zip(counts[:times], counts[times:]))

    begin_time = time.time()

    msg = f"| Partition: {bitstring_range}, Measure: {measure}"

    if backend not in PostProcessingBackendStatement[1]:
        warnings.warn(
            f"Unknown backend '{backend}', using {DEFAULT_PROCESS_BACKEND} instead.",
        )
        backend = DEFAULT_PROCESS_BACKEND

    # if not RUST_AVAILABLE and backend == "Rust":
    #     warnings.warn(
    #         "Rust is not available, using Cython or Python to calculate purity cell."
    #         + f"Check the error: {FAILED_RUST_IMPORT}",
    #         PostProcessingRustUnavailableWarning,
    #     )
    #     backend = "Cython" if CYTHON_AVAILABLE else "Python"
    if not CYTHON_AVAILABLE and backend == "Cython":
        warnings.warn(
            "Cython is not available, using Python to calculate purity cell."
            + f"Check the error: {FAILED_PYX_IMPORT}",
            PostProcessingCythonUnavailableWarning,
        )
        # backend = "Rust" if RUST_AVAILABLE else "Python"
        backend = "Python"

    cell_calculation = (
        echo_cell_cy
        if backend == "Cython"
        # else (echo_cell_rust if backend == "Rust" else echo_cell_py)
        else echo_cell_py
    )

    if launch_worker == 1:
        echo_cell_items = []
        msg += f", single process, {times} overlaps, it will take a lot of time."
        print(msg)
        for i, (c1, c2) in enumerate(counts_pair):
            echo_cell_items.append(
                cell_calculation(i, c1, c2, bitstring_range, subsystem_size)
            )

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


# def overlap_echo_allrust(
#     shots: int,
#     counts: list[dict[str, int]],
#     degree: Union[tuple[int, int], int],
#     measure: tuple[int, int] = None,
# ) -> tuple[dict[int, float], tuple[int, int], tuple[int, int], str, float]:
#     """The core function of entangled entropy.

#     Args:
#         shots (int): Shots of the experiment on quantum machine.
#         counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
#         degree (Union[tuple[int, int], int]): Degree of the subsystem.
#         measure (tuple[int, int], optional):
#             Measuring range on quantum circuits. Defaults to None.
#         backend (PostProcessingBackendLabel, optional):
#             The backend of the process, 'Cython', 'Rust' or 'Python'.
#             Defaults to DEFAULT_PROCESS_BACKEND.

#     Raises:
#         ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
#         ValueError: Measure range does not contain subsystem.

#     Returns:
#         tuple[dict[int, float], tuple[int, int], tuple[int, int], str, float]:
#             Purity of each cell, Partition range, Measuring range, Message, Time to calculate.
#     """

#     return overlap_echo_core_rust_source(shots, counts, degree, measure)


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

    # if backend == "Rust":
    #     if RUST_AVAILABLE:
    #         return eoverlap_echo_core_allrust(shots, counts, degree, measure)
    #     backend = "Cython" if CYTHON_AVAILABLE else "Python"
    #     warnings.warn(
    #         f"Rust is not available, using {backend} to calculate purity cell."
    #         + f" Check the error: {FAILED_RUST_IMPORT}",
    #         PostProcessingRustUnavailableWarning,
    #     )

    return overlap_echo_core_pycyrust(
        shots, counts, degree, measure, multiprocess_pool_size, backend
    )


def randomized_overlap_echo(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]] = None,
    measure: Optional[tuple[int, int]] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    workers_num: Optional[int] = None,
    pbar: Optional[tqdm.tqdm] = None,
) -> dict[str, float]:
    """Calculate entangled entropy.

    - Reference:
        - Used in:
            Statistical correlations between locally randomized measurements:
            A toolbox for probing entanglement in many-body quantum states -
            A. Elben, B. Vermersch, C. F. Roos, and P. Zoller,
            [PhysRevA.99.052323](https://doi.org/10.1103/PhysRevA.99.052323)

        - `bibtex`:

    ```bibtex
        @article{PhysRevA.99.052323,
            title = {Statistical correlations between locally randomized measurements:
            A toolbox for probing entanglement in many-body quantum states},
            author = {Elben, A. and Vermersch, B. and Roos, C. F. and Zoller, P.},
            journal = {Phys. Rev. A},
            volume = {99},
            issue = {5},
            pages = {052323},
            numpages = {12},
            year = {2019},
            month = {May},
            publisher = {American Physical Society},
            doi = {10.1103/PhysRevA.99.052323},
            url = {https://link.aps.org/doi/10.1103/PhysRevA.99.052323}
        }
        ```

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
        pbar (Optional[tqdm.tqdm], optional): Progress bar. Defaults to None.
        all_system_source (Optional['EntropyRandomizedAnalysis'], optional):
            The source of the all system. Defaults to None.
        use_cython (bool, optional): Use cython to calculate purity cell. Defaults to True.

    Returns:
        dict[str, float]: A dictionary contains purity, entropy,
            a list of each overlap, puritySD, degree, actual measure range, bitstring range.
    """

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(f"Calculate overlap with {len(counts)} counts.")

    (
        echo_cell_dict,
        bitstring_range,
        measure_range,
        _msg_of_process,
        taken,
    ) = overlap_echo_core(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        backend=backend,
        multiprocess_pool_size=workers_num,
    )
    echo_cell_list: Union[list[float], list[np.float64]] = list(
        echo_cell_dict.values()
    )  # type: ignore

    echo = np.mean(echo_cell_list, dtype=np.float64)
    purity_sd = np.std(echo_cell_list, dtype=np.float64)

    quantity = {
        "echo": echo,
        "echoCells": echo_cell_dict,
        "echoSD": purity_sd,
        "degree": degree,
        "measureActually": measure_range,
        "bitStringRange": bitstring_range,
        "countsNum": len(counts),
        "takingTime": taken,
    }

    return quantity
