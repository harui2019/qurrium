"""
================================================================
Postprocessing - Renyi Entropy - Randomized Measure - 
Entangled Entropy
(:mod:`qurry.process.randomized_measure.entangled_entropy`)
================================================================

"""

import time
import warnings
from typing import Union, Optional, Literal, TypedDict
import numpy as np
import tqdm

from .purity_cell import (
    purity_cell_py,
    purity_cell_cy,
    purity_cell_rust,
    CYTHON_AVAILABLE,
    FAILED_PYX_IMPORT,
)
from .error_mitigation import depolarizing_error_mitgation
from ..utils import (
    cycling_slice as cycling_slice_py,
    qubit_selector,
)
from ...exceptions import (
    QurryCythonUnavailableWarning,
    QurryRustImportError,
    QurryRustUnavailableWarning,
)
from ...tools import (
    ProcessManager,
    workers_distribution,
)


try:
    # Proven import point for rust modules
    # from ..boorust.randomized import (  # type: ignore
    #     purity_cell_rust as purity_cell_rust_source,  # type: ignore
    #     entangled_entropy_core_rust as entangled_entropy_core_rust_source,  # type: ignore
    # )

    from ..boorust import randomized  # type: ignore

    entangled_entropy_core_rust_source = randomized.entangled_entropy_core_rust

    RUST_AVAILABLE = True
    FAILED_RUST_IMPORT = None
except ImportError as err:
    RUST_AVAILABLE = False
    FAILED_RUST_IMPORT = err

    def entangled_entropy_core_rust_source(*args, **kwargs):
        """Dummy function for entangled_entropy_core_rust."""
        raise QurryRustImportError(
            "Rust is not available, using python to calculate entangled entropy."
        ) from FAILED_RUST_IMPORT


ExistingProcessBackendLabel = Literal["Cython", "Rust", "Python"]
BackendAvailabilities: dict[ExistingProcessBackendLabel, Union[bool, ImportError]] = {
    "Cython": CYTHON_AVAILABLE if CYTHON_AVAILABLE else FAILED_PYX_IMPORT,
    "Rust": RUST_AVAILABLE if RUST_AVAILABLE else FAILED_RUST_IMPORT,
    "Python": True,
}
DEFAULT_PROCESS_BACKEND: ExistingProcessBackendLabel = (
    "Rust" if RUST_AVAILABLE else ("Cython" if CYTHON_AVAILABLE else "Python")
)


def entangled_entropy_core_pycyrust(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Optional[tuple[int, int]] = None,
    multiprocess_pool_size: Optional[int] = None,
    backend: ExistingProcessBackendLabel = "Cython",
) -> tuple[dict[int, float], tuple[int, int], tuple[int, int], str, float]:
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


def entangled_entropy_core_allrust(
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

    if isinstance(measure, list):
        measure = tuple(measure)

    if backend == "Rust":
        if RUST_AVAILABLE:
            return entangled_entropy_core_allrust(shots, counts, degree, measure)
        backend = "Cython" if CYTHON_AVAILABLE else "Python"
        warnings.warn(
            f"Rust is not available, using {backend} to calculate purity cell."
            + f" Check the error: {FAILED_RUST_IMPORT}",
            QurryRustUnavailableWarning,
        )

    return entangled_entropy_core_pycyrust(
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


class ExistingAllSystemSource(TypedDict):
    purityCellsAllSys: dict[int, float]
    bitStringRange: tuple[int, int]
    measureActually: tuple[int, int]
    source: str


def randomized_entangled_entropy_mitigated(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Optional[tuple[int, int]] = None,
    backend: ExistingProcessBackendLabel = DEFAULT_PROCESS_BACKEND,
    workers_num: Optional[int] = None,
    existed_all_system: Optional[ExistingAllSystemSource] = None,
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
        existed_all_system (Optional[ExistingAllSystemSource], optional):
            Existing all system source. Defaults to None.
        pbar (Optional[tqdm.tqdm], optional): Progress bar. Defaults to None.

    Returns:
        dict[str, float]: A dictionary contains
            purity, entropy, a list of each overlap, puritySD,
            purity of all system, entropy of all system,
            a list of each overlap in all system, puritySD of all system,
            degree, actual measure range, actual measure range in all system, bitstring range.
    """
    null_counts = [i for i, c in enumerate(counts) if len(c) == 0]
    if len(null_counts) > 0:
        return {
            # target system
            "purity": np.NaN,
            "entropy": np.NaN,
            "purityCells": {},
            "puritySD": np.NaN,
            "entropySD": np.NaN,
            "bitStringRange": (),
            # all system
            "allSystemSource": "Null counts exist, no measure.",
            "purityAllSys": np.NaN,
            "entropyAllSys": np.NaN,
            "purityCellsAllSys": {},
            "puritySDAllSys": np.NaN,
            "entropySDAllSys": np.NaN,
            "bitsStringRangeAllSys": (),
            # mitigated
            "errorRate": np.NaN,
            "mitigatedPurity": np.NaN,
            "mitigatedEntropy": np.NaN,
            # info
            "degree": degree,
            "num_qubits": np.NaN,
            "measure": ("The following is the index of null counts.", null_counts),
            "measureActually": (),
            "measureActuallyAllSys": (),
            "countsNum": len(counts),
            "takingTime": 0,
            "takingTimeAllSys": 0,
        }

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(f"Calculate specific degree {degree} by {backend}.")
    (
        purity_cell_dict,
        bitstring_range,
        measure_range,
        msg,
        taken,
    ) = entangled_entropy_core(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        backend=backend,
        multiprocess_pool_size=workers_num,
    )
    purity_cell_list = list(purity_cell_dict.values())

    if existed_all_system is None:
        if isinstance(pbar, tqdm.tqdm):
            pbar.set_description_str(f"Calculate all system by {backend}.")
        (
            purity_cell_dict_allsys,
            bitstring_range_allsys,
            measure_range_allsys,
            _msg_allsys,
            taken_allsys,
        ) = entangled_entropy_core(
            shots=shots,
            counts=counts,
            degree=None,
            measure=measure,
            backend=backend,
            multiprocess_pool_size=workers_num,
        )
        purity_cell_list_allsys = list(purity_cell_dict_allsys.values())
        source = "independent"
    else:
        for k, msg in [
            ("purityCellsAllSys", "purityCellsAllSys is not in existed_all_system."),
            ("bitStringRange", "bitStringRange is not in existed_all_system."),
            ("measureActually", "measureActually is not in existed_all_system."),
            ("source", "source is not in existed_all_system."),
        ]:
            assert k in existed_all_system, msg

        source = existed_all_system["source"]
        if isinstance(pbar, tqdm.tqdm):
            pbar.set_description_str(f"Using existing all system from '{source}'")
        purity_cell_dict_allsys = existed_all_system["purityCellsAllSys"]
        purity_cell_list_allsys = list(purity_cell_dict_allsys.values())
        bitstring_range_allsys = existed_all_system["bitStringRange"]
        measure_range_allsys = existed_all_system["measureActually"]
        _msg_allsys = f"Use all system from {source}."
        taken_allsys = 0

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(
            f"Preparing error mitigation of {bitstring_range} on {measure}"
        )

    purity: float = np.mean(purity_cell_list, dtype=np.float64)
    purity_allsys: float = np.mean(purity_cell_list_allsys, dtype=np.float64)
    purity_sd = np.std(purity_cell_list, dtype=np.float64)
    purity_sd_allsys = np.std(purity_cell_list_allsys, dtype=np.float64)

    entropy = -np.log2(purity, dtype=np.float64)
    entropy_sd = purity_sd / np.log(2) / purity
    entropy_allsys = -np.log2(purity_allsys, dtype=np.float64)
    entropy_sd_allsys = purity_sd_allsys / np.log(2) / purity_allsys

    if measure is None:
        measure_info = ("not specified, use all qubits", measure_range)
    else:
        measure_info = ("measure range:", measure)

    num_qubits = len(list(counts[0].keys())[0])
    if isinstance(degree, tuple):
        subsystem = max(degree) - min(degree)
    else:
        subsystem = degree

    error_mitgation_info = depolarizing_error_mitgation(
        meas_system=purity,
        all_system=purity_allsys,
        n_a=subsystem,
        system_size=num_qubits,
    )

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(msg[2:-1] + " with mitigation.")

    quantity = {
        # target system
        "purity": purity,
        "entropy": entropy,
        "purityCells": purity_cell_dict,
        "puritySD": purity_sd,
        "entropySD": entropy_sd,
        "bitStringRange": bitstring_range,
        # all system
        "allSystemSource": source,  # 'independent' or 'header of analysis'
        "purityAllSys": purity_allsys,
        "entropyAllSys": entropy_allsys,
        "purityCellsAllSys": purity_cell_dict_allsys,
        "puritySDAllSys": purity_sd_allsys,
        "entropySDAllSys": entropy_sd_allsys,
        "bitsStringRangeAllSys": bitstring_range_allsys,
        # mitigated
        "errorRate": error_mitgation_info["errorRate"],
        "mitigatedPurity": error_mitgation_info["mitigatedPurity"],
        "mitigatedEntropy": error_mitgation_info["mitigatedEntropy"],
        # info
        "degree": degree,
        "num_qubits": num_qubits,
        "measure": measure_info,
        "measureActually": measure_range,
        "measureActuallyAllSys": measure_range_allsys,
        "countsNum": len(counts),
        "takingTime": taken,
        "takingTimeAllSys": taken_allsys,
    }
    return quantity
