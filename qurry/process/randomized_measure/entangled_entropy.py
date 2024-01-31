"""
================================================================
Postprocessing - Randomized Measure - Entangled Entropy
(:mod:`qurry.process.randomized_measure.entangled_entropy`)
================================================================

"""

from typing import Union, Optional, Literal, TypedDict
import numpy as np
import tqdm

from .entropy_core import (
    entangled_entropy_core,
    ExistingProcessBackendLabel,
    DEFAULT_PROCESS_BACKEND,
)
from .error_mitigation import depolarizing_error_mitgation


class RandomizedEntangledEntropyComplex(TypedDict):
    """The result of the analysis."""

    purity: Union[np.float64, float]
    entropy: Union[np.float64, float]
    puritySD: Union[np.float64, float]
    entropySD: Union[np.float64, float]
    purityCells: Union[dict[int, np.float64], dict[int, float]]
    bitStringRange: Union[tuple[int, int], tuple[()]]

    allSystemSource: Union[str, Literal["independent"]]
    purityAllSys: Union[np.float64, float]
    entropyAllSys: Union[np.float64, float]
    puritySDAllSys: Union[np.float64, float]
    entropySDAllSys: Union[np.float64, float]
    purityCellsAllSys: Union[dict[int, np.float64], dict[int, float]]
    bitsStringRangeAllSys: Union[tuple[int, int], tuple[()], None]

    errorRate: Union[np.float64, float]
    mitigatedPurity: Union[np.float64, float]
    mitigatedEntropy: Union[np.float64, float]

    degree: Optional[Union[tuple[int, int], int]]
    num_qubits: int
    measure: tuple[str, Union[list[int], tuple[int, int]]]
    measureActually: Union[tuple[int, int], tuple[()]]
    measureActuallyAllSys: Union[tuple[int, int], tuple[()], None]

    countsNum: int
    takingTime: Union[np.float64, float]
    takingTimeAllSys: Union[np.float64, float]


def randomized_entangled_entropy(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Optional[tuple[int, int]] = None,
    backend: ExistingProcessBackendLabel = DEFAULT_PROCESS_BACKEND,
    workers_num: Optional[int] = None,
    pbar: Optional[tqdm.tqdm] = None,
) -> dict[str, Union[np.float64, float]]:
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
        dict[str,Union[np.float64, float]]: A dictionary contains purity, entropy,
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
    purity_cell_list: Union[list[float], list[np.float64]] = list(
        purity_cell_dict.values()
    )  # type: ignore

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
    """Existing all system source."""

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
) -> RandomizedEntangledEntropyComplex:
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
        dict[str,Union[np.float64, float]]: A dictionary contains
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
            "num_qubits": 0,
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
    purity_cell_list: Union[list[float], list[np.float64]] = list(
        purity_cell_dict.values()
    )  # type: ignore

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
        purity_cell_list_allsys: Union[list[float], list[np.float64]] = list(purity_cell_dict_allsys.values())  # type: ignore
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

    purity: Union[np.float64, float] = np.mean(purity_cell_list, dtype=np.float64)
    purity_allsys: Union[np.float64, float] = np.mean(
        purity_cell_list_allsys, dtype=np.float64
    )
    purity_sd: Union[np.float64, float] = np.std(purity_cell_list, dtype=np.float64)
    purity_sd_allsys: Union[np.float64, float] = np.std(
        purity_cell_list_allsys, dtype=np.float64
    )

    entropy: Union[np.float64, float] = -np.log2(purity, dtype=np.float64)
    entropy_sd: Union[np.float64, float] = purity_sd / np.log(2) / purity
    entropy_allsys: Union[np.float64, float] = -np.log2(purity_allsys, dtype=np.float64)
    entropy_sd_allsys: Union[np.float64, float] = (
        purity_sd_allsys / np.log(2) / purity_allsys
    )

    if measure is None:
        measure_info = ("not specified, use all qubits", measure_range)
    else:
        measure_info = ("measure range:", measure)

    num_qubits = len(list(counts[0].keys())[0])
    if degree is None:
        degree = num_qubits
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

    quantity: RandomizedEntangledEntropyComplex = {
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
