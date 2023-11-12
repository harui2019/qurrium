"""
================================================================
Renyi Entropy Postprocessing
(:mod:`qurry.qurrent.postprocess`)
================================================================

"""
import time
import warnings
from typing import Union, Optional, Literal, overload
import numpy as np
import tqdm

from ..exceptions import (
    QurryCythonImportError,
    QurryCythonUnavailableWarning,
    QurryRustImportError,
    QurryRustUnavailableWarning,
)
from ..qurrium import qubit_selector
from ..qurrium.utils.randomized import (
    ensemble_cell as ensemble_cell_py,
    cycling_slice as cycling_slice_py,
)
from ..tools import (
    ProcessManager,
    workers_distribution,
)

try:
    from ..boost.randomized import purityCellCore  # type: ignore

    CYTHON_AVAILABLE = True
    FAILED_PYX_IMPORT = None
except ImportError as err:
    FAILED_PYX_IMPORT = err
    CYTHON_AVAILABLE = False
    # pylint: disable=invalid-name, unused-argument

    def purityCellCore(*args, **kwargs):
        """Dummy function for purityCellCore."""
        raise QurryCythonImportError(
            "Cython is not available, using python to calculate purity cell."
            + f" More infomation about this error: {FAILED_PYX_IMPORT}",
        )

    # pylint: enable=invalid-name, unused-argument

try:
    # Proven import point for rust modules
    # from ..boorust.randomized import (  # type: ignore
    #     purity_cell_rust as purity_cell_rust_source,  # type: ignore
    #     entangled_entropy_core_rust as entangled_entropy_core_rust_source,  # type: ignore
    # )

    from ..boorust import randomized  # type: ignore

    purity_cell_rust_source = randomized.purity_cell_rust
    entangled_entropy_core_rust_source = randomized.entangled_entropy_core_rust

    RUST_AVAILABLE = True
    FAILED_RUST_IMPORT = None
except ImportError as err:
    RUST_AVAILABLE = False
    FAILED_RUST_IMPORT = err

    def purity_cell_rust_source(*args, **kwargs):
        """Dummy function for purity_cell_rust."""
        raise QurryRustImportError(
            "Rust is not available, using python to calculate purity cell."
            + f" More infomation about this error: {err}",
        )

    def entangled_entropy_core_rust_source(*args, **kwargs):
        """Dummy function for entangled_entropy_core_rust."""
        raise QurryRustImportError(
            "Rust is not available, using python to calculate entangled entropy."
            + f" More infomation about this error: {err}",
        )


ExistingProcessBackendLabel = Literal["Cython", "Rust", "Python"]
BackendAvailabilities: dict[ExistingProcessBackendLabel, Union[bool, ImportError]] = {
    "Cython": CYTHON_AVAILABLE if CYTHON_AVAILABLE else FAILED_PYX_IMPORT,
    "Rust": RUST_AVAILABLE if RUST_AVAILABLE else FAILED_RUST_IMPORT,
    "Python": True,
}
DEFAULT_PROCESS_BACKEND: ExistingProcessBackendLabel = (
    "Rust" if RUST_AVAILABLE else ("Cython" if CYTHON_AVAILABLE else "Python")
)


# Hadamard test
def hadamard_entangled_entropy(
    shots: int,
    counts: list[dict[str, int]],
) -> dict[str, float]:
    """Calculate entangled entropy with more information combined.

    - Which entropy:

        The entropy we compute is the Second Order Rényi Entropy.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.

    Raises:
        Warning: Expected '0' and '1', but there is no such keys

    Returns:
        dict[str, float]: Quantity of the experiment.
    """

    purity = -100
    entropy = -100
    only_counts = counts[0]
    sample_shots = sum(only_counts.values())
    assert (
        sample_shots == shots
    ), f"shots {shots} does not match sample_shots {sample_shots}"

    is_zero_include = "0" in only_counts
    is_one_include = "1" in only_counts
    if is_zero_include and is_one_include:
        purity = (only_counts["0"] - only_counts["1"]) / shots
    elif is_zero_include:
        purity = only_counts["0"] / shots
    elif is_one_include:
        purity = only_counts["1"] / shots
    else:
        purity = np.Nan
        raise ValueError("Expected '0' and '1', but there is no such keys")

    entropy = -np.log2(purity)
    quantity = {
        "purity": purity,
        "entropy": entropy,
    }
    return quantity


# Randomized measure
def purity_cell_py(
    idx: int,
    single_counts: dict[str, int],
    bitstring_range: tuple[int, int],
    subsystem_size: int,
) -> tuple[int, float]:
    """Calculate the purity cell, one of overlap, of a subsystem by Python.

    Args:
        idx (int): Index of the cell (counts).
        single_counts (dict[str, int]): Counts measured by the single quantum circuit.
        bitstring_range (tuple[int, int]): The range of the subsystem.
        subsystem_size (int): Subsystem size included.

    Returns:
        tuple[int, float]: Index, one of overlap purity.
    """

    shots = sum(single_counts.values())

    _dummy_string = "".join(str(ds) for ds in range(subsystem_size))
    if _dummy_string[bitstring_range[0] : bitstring_range[1]] == cycling_slice_py(
        _dummy_string, bitstring_range[0], bitstring_range[1], 1
    ):
        single_counts_under_degree = dict.fromkeys(
            [k[bitstring_range[0] : bitstring_range[1]] for k in single_counts], 0
        )
        for bitstring in list(single_counts):
            single_counts_under_degree[
                bitstring[bitstring_range[0] : bitstring_range[1]]
            ] += single_counts[bitstring]

    else:
        single_counts_under_degree = dict.fromkeys(
            [
                cycling_slice_py(k, bitstring_range[0], bitstring_range[1], 1)
                for k in single_counts
            ],
            0,
        )
        for bitstring in list(single_counts):
            single_counts_under_degree[
                cycling_slice_py(bitstring, bitstring_range[0], bitstring_range[1], 1)
            ] += single_counts[bitstring]

    _purity_cell = np.float64(0)
    for s_ai, s_ai_meas in single_counts_under_degree.items():
        for s_aj, s_aj_meas in single_counts_under_degree.items():
            _purity_cell += ensemble_cell_py(
                s_ai, s_ai_meas, s_aj, s_aj_meas, subsystem_size, shots
            )

    return idx, _purity_cell


def purity_cell_cy(
    idx: int,
    single_counts: dict[str, int],
    bitstring_range: tuple[int, int],
    subsystem_size: int,
) -> tuple[int, float]:
    """Calculate the purity cell, one of overlap, of a subsystem by Cython.

    Args:
        idx (int): Index of the cell (counts).
        single_counts (dict[str, int]): Counts measured by the single quantum circuit.
        bitstring_range (tuple[int, int]): The range of the subsystem.
        subsystem_size (int): Subsystem size included.

    Returns:
        tuple[int, float]: Index, one of overlap purity.
    """

    return idx, purityCellCore(dict(single_counts), bitstring_range, subsystem_size)


def purity_cell_rust(
    idx: int,
    single_counts: dict[str, int],
    bitstring_range: tuple[int, int],
    subsystem_size: int,
) -> tuple[int, float]:
    """Calculate the purity cell, one of overlap, of a subsystem by Rust.

    Args:
        idx (int): Index of the cell (counts).
        single_counts (dict[str, int]): Counts measured by the single quantum circuit.
        bitstring_range (tuple[int, int]): The range of the subsystem.
        subsystem_size (int): Subsystem size included.

    Returns:
        tuple[int, float]: Index, one of overlap purity.
    """

    return purity_cell_rust_source(idx, single_counts, bitstring_range, subsystem_size)


def purity_cell(
    idx: int,
    single_counts: dict[str, int],
    bitstring_range: tuple[int, int],
    subsystem_size: int,
    backend: ExistingProcessBackendLabel = DEFAULT_PROCESS_BACKEND,
) -> tuple[int, float]:
    """Calculate the purity cell, one of overlap, of a subsystem.

    Args:
        idx (int): Index of the cell (counts).
        single_counts (dict[str, int]): Counts measured by the single quantum circuit.
        bitstring_range (tuple[int, int]): The range of the subsystem.
        subsystem_size (int): Subsystem size included.
        backend (ExistingProcessBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.

    Returns:
        tuple[int, float]: Index, one of overlap purity.
    """

    if backend == "Cython":
        return purity_cell_cy(idx, single_counts, bitstring_range, subsystem_size)
    if backend == "Rust":
        return purity_cell_rust(idx, single_counts, bitstring_range, subsystem_size)
    return purity_cell_py(idx, single_counts, bitstring_range, subsystem_size)


def entangled_entropy_core_pycy(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Optional[tuple[int, int]] = None,
    multiprocess_pool_size: Optional[int] = None,
    backend: ExistingProcessBackendLabel = "Cython",
) -> tuple[dict[int, float], tuple[int, int], tuple[int, int], str, float]:
    """The core function of entangled entropy by Cython or Python.

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
        use_cython (bool, optional): Use cython to calculate purity cell. Defaults to True.
        _hide_print (bool, optional): Hide print. Defaults to False.

    Raises:
        ValueError: Get degree neither 'int' nor 'tuple[int, int]'.
        ValueError: Measure range does not contain subsystem.

    Returns:
        tuple[dict[int, float], tuple[int, int], tuple[int, int], str, float]:
            Purity of each cell, Partition range, Measuring range, Message, Time to calculate.
    """

    # check shots
    sample_shots = sum(counts[0].values())
    assert (
        sample_shots == shots
    ), f"shots {shots} does not match sample_shots {sample_shots}"

    # Determine worker number
    launch_worker = workers_distribution(multiprocess_pool_size)

    # Determine subsystem size
    allsystem_size = len(list(counts[0].keys())[0])

    # Determine degree
    degree = qubit_selector(allsystem_size, degree=degree)
    subsystems_size = max(degree) - min(degree)

    bitstring_range = degree
    bitstring_check = {
        "b > a": (bitstring_range[1] > bitstring_range[0]),
        "a >= -allsystemSize": bitstring_range[0] >= -allsystem_size,
        "b <= allsystemSize": bitstring_range[1] <= allsystem_size,
        "b-a <= allsystemSize": (
            (bitstring_range[1] - bitstring_range[0]) <= allsystem_size
        ),
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
    _dummy_string_slice = cycling_slice_py(
        _dummy_string, bitstring_range[0], bitstring_range[1], 1
    )
    is_avtive_cycling_slice = (
        _dummy_string[bitstring_range[0] : bitstring_range[1]] != _dummy_string_slice
    )
    if is_avtive_cycling_slice:
        assert len(_dummy_string_slice) == subsystems_size, (
            f"| All system size '{subsystems_size}' "
            + f"does not match dummyStringSlice '{_dummy_string_slice}'"
        )

    if backend not in BackendAvailabilities:
        warnings.warn(
            f"Unknown backend '{backend}', using {DEFAULT_PROCESS_BACKEND} instead.",
        )
        backend = DEFAULT_PROCESS_BACKEND

    if not RUST_AVAILABLE and backend == "Rust":
        warnings.warn(
            "Rust is not available, using Cython or Python to calculate purity cell."
            + f"Check the error: {FAILED_RUST_IMPORT}",
            QurryRustUnavailableWarning,
        )
        backend = "Cython" if CYTHON_AVAILABLE else "Python"
    if not CYTHON_AVAILABLE and backend == "Cython":
        warnings.warn(
            "Cython is not available, using Python to calculate purity cell."
            + f"Check the error: {FAILED_PYX_IMPORT}",
            QurryCythonUnavailableWarning,
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
            purity_cell_items.append(
                cell_calculation(i, c, bitstring_range, subsystems_size)
            )
        taken = round(time.time() - begin, 3)

    else:
        msg += f", {launch_worker} workers, {times} overlaps."

        pool = ProcessManager(launch_worker)
        purity_cell_items = pool.starmap(
            cell_calculation,
            [(i, c, bitstring_range, subsystems_size) for i, c in enumerate(counts)],
        )
        taken = round(time.time() - begin, 3)

    purity_cell_dict = dict(purity_cell_items)
    return purity_cell_dict, bitstring_range, measure, msg, taken


def entangled_entropy_core_rust(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Optional[tuple[int, int]] = None,
) -> tuple[dict[int, float], tuple[int, int], tuple[int, int], str, float]:
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
    measure: Optional[tuple[int, int]] = None,
    backend: ExistingProcessBackendLabel = DEFAULT_PROCESS_BACKEND,
    multiprocess_pool_size: Optional[int] = None,
) -> tuple[dict[int, float], tuple[int, int], tuple[int, int], str, float]:
    """The core function of entangled entropy.

    Args:
        shots (int): Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
        degree (Optional[Union[tuple[int, int], int]]): Degree of the subsystem.
        measure (Optional[tuple[int, int]], optional):
            Measuring range on quantum circuits. Defaults to None.
        backend (ExistingProcessBackendLabel, optional):
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

    if backend == "Rust":
        if RUST_AVAILABLE:
            return entangled_entropy_core_rust(shots, counts, degree, measure)
        backend = "Cython" if CYTHON_AVAILABLE else "Python"
        warnings.warn(
            f"Rust is not available, using {backend} to calculate purity cell."
            + f" Check the error: {FAILED_RUST_IMPORT}",
            QurryRustUnavailableWarning,
        )

    return entangled_entropy_core_pycy(
        shots, counts, degree, measure, multiprocess_pool_size, backend
    )


def randomized_entangled_entropy(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Optional[tuple[int, int]] = None,
    backend: ExistingProcessBackendLabel = DEFAULT_PROCESS_BACKEND,
    workers_num: Optional[int] = None,
    pbar: Optional[tqdm.tqdm] = None,
) -> dict[str, float]:
    """Calculate entangled entropy.

    - Which entropy:

        The entropy we compute is the Second Order Rényi Entropy.

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
        degree (Optional[Union[tuple[int, int], int]]): Degree of the subsystem.
        measure (Optional[tuple[int, int]], optional):
            Measuring range on quantum circuits. Defaults to None.
        backend (ExistingProcessBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
        workers_num (Optional[int], optional):
            Number of multi-processing workers, it will be ignored if backend is Rust.
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts by `os.cpu_count()`.
            Defaults to None.
        pbar (Optional[tqdm.tqdm], optional): Progress bar. Defaults to None.

    Returns:
        dict[str, float]: A dictionary contains purity, entropy,
            a list of each overlap, puritySD, degree, actual measure range, bitstring range.
    """

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(f"Calculate specific degree {degree}.")
    (
        purity_cell_dict,
        bitstring_range,
        measure_range,
        _msg,
        _taken,
    ) = entangled_entropy_core(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        backend=backend,
        multiprocess_pool_size=workers_num,
    )
    purity_cell_list = list(purity_cell_dict.values())

    purity = np.mean(purity_cell_list, dtype=np.float64)
    purity_sd = np.std(purity_cell_list, dtype=np.float64)
    entropy = -np.log2(purity, dtype=np.float64)
    entropy_sd = purity_sd / np.log(2) / purity

    quantity = {
        "purity": purity,
        "entropy": entropy,
        "purityCells": purity_cell_dict,
        "puritySD": purity_sd,
        "entropySD": entropy_sd,
        "degree": degree,
        "measureActually": measure_range,
        "bitStringRange": bitstring_range,
        "countsNum": len(counts),
    }

    return quantity


# Randomized measure error mitigation
@overload
def solve_p(meas_series: np.ndarray, n_a: int) -> tuple[np.ndarray, np.ndarray]:
    ...


@overload
def solve_p(meas_series: float, n_a: int) -> tuple[float, float]:
    ...


def solve_p(meas_series, n_a):
    """Solve the equation of p from all system size and subsystem size.

    Args:
        meas_series (Union[np.ndarray, float]): Measured series.
        n_a (int): Subsystem size.

    Returns:
        Union[tuple[np.ndarray, np.ndarray], tuple[float, float]]:
            Two solutions of p.
    """
    b = np.float64(1) / 2 ** (n_a - 1) - 2
    a = np.float64(1) + 1 / 2**n_a - 1 / 2 ** (n_a - 1)
    c = 1 - meas_series
    ppser = (-b + np.sqrt(b**2 - 4 * a * c)) / 2 / a
    pnser = (-b - np.sqrt(b**2 - 4 * a * c)) / 2 / a

    return ppser, pnser


@overload
def mitigation_equation(
    pser: np.ndarray, meas_series: np.ndarray, n_a: int
) -> np.ndarray:
    ...


@overload
def mitigation_equation(pser: float, meas_series: float, n_a: int) -> float:
    ...


def mitigation_equation(pser, meas_series, n_a):
    """Calculate the mitigation equation.

    Args:
        pser (Union[np.ndarray, float]): Solution of p.
        meas_series (Union[np.ndarray, float]): Measured series.
        n_a (int): Subsystem size.

    Returns:
        Union[np.ndarray, float]: Mitigated series.
    """
    psq = np.square(pser, dtype=np.float64)
    return (meas_series - psq / 2**n_a - (pser - psq) / 2 ** (n_a - 1)) / np.square(
        1 - pser, dtype=np.float64
    )


@overload
def depolarizing_error_mitgation(
    meas_system: float,
    all_system: float,
    n_a: int,
    system_size: int,
) -> dict[str, float]:
    ...


@overload
def depolarizing_error_mitgation(
    meas_system: np.ndarray,
    all_system: np.ndarray,
    n_a: int,
    system_size: int,
) -> dict[str, np.ndarray]:
    ...


def depolarizing_error_mitgation(meas_system, all_system, n_a, system_size):
    """Depolarizing error mitigation.

    Args:
        meas_system (Union[float, np.ndarray]): Value of the measured subsystem.
        all_system (Union[float, np.ndarray]): Value of the whole system.
        n_a (int): The size of the subsystem.
        system_size (int): The size of the system.

    Returns:
        Union[dict[str, float], dict[str, np.ndarray]]:
            Error rate, mitigated purity, mitigated entropy.
    """

    _, pn = solve_p(all_system, system_size)
    mitiga = mitigation_equation(pn, meas_system, n_a)

    return {
        "errorRate": pn,
        "mitigatedPurity": mitiga,
        "mitigatedEntropy": -np.log2(mitiga, dtype=np.float64),
    }
