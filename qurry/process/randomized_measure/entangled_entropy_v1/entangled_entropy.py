"""
=========================================================================================
Postprocessing - Randomized Measure - Entangled Entropy V1 - Entangled Entropy Deprecated
(:mod:`qurry.process.randomized_measure.entangled_entropy_v1.entangled_entropy`)
=========================================================================================

"""

from typing import Union, Optional
import numpy as np
import tqdm

from .entropy_core import entangled_entropy_core, DEFAULT_PROCESS_BACKEND
from .container import (
    RandomizedEntangledEntropyComplex,
    RandomizedEntangledEntropyMitigatedComplex,
    ExistingAllSystemSource,
)
from ..entangled_entropy.error_mitigation import depolarizing_error_mitgation
from ...availability import PostProcessingBackendLabel


def randomized_entangled_entropy_deprecated(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Optional[tuple[int, int]] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    workers_num: Optional[int] = None,
    pbar: Optional[tqdm.tqdm] = None,
) -> RandomizedEntangledEntropyComplex:
    """Calculate entangled entropy.
    The entropy we compute is the Second Order Rényi Entropy.

    .. note::

        - Probing Rényi entanglement entropy via randomized measurements -
        Tiff Brydges, Andreas Elben, Petar Jurcevic, Benoît Vermersch,
        Christine Maier, Ben P. Lanyon, Peter Zoller, Rainer Blatt ,and Christian F. Roos ,
        [doi:10.1126/science.aau4963](
            https://www.science.org/doi/abs/10.1126/science.aau4963)

    .. code-block:: bibtex

        @article{doi:10.1126/science.aau4963,
            author = {Tiff Brydges  and Andreas Elben  and Petar Jurcevic
                and Benoît Vermersch  and Christine Maier  and Ben P. Lanyon
                and Peter Zoller  and Rainer Blatt  and Christian F. Roos },
            title = {Probing Rényi entanglement entropy via randomized measurements},
            journal = {Science},
            volume = {364},
            number = {6437},
            pages = {260-263},
            year = {2019},
            doi = {10.1126/science.aau4963},
            URL = {https://www.science.org/doi/abs/10.1126/science.aau4963},
            eprint = {https://www.science.org/doi/pdf/10.1126/science.aau4963},
            abstract = {Quantum systems are predicted to be better at information
            processing than their classical counterparts, and quantum entanglement
            is key to this superior performance. But how does one gauge the degree
            of entanglement in a system? Brydges et al. monitored the build-up of
            the so-called Rényi entropy in a chain of up to 10 trapped calcium ions,
            each of which encoded a qubit. As the system evolved,
            interactions caused entanglement between the chain and the rest of
            the system to grow, which was reflected in the growth of
            the Rényi entropy. Science, this issue p. 260 The buildup of entropy
            in an ion chain reflects a growing entanglement between the chain
            and its complement. Entanglement is a key feature of many-body quantum systems.
            Measuring the entropy of different partitions of a quantum system
            provides a way to probe its entanglement structure.
            Here, we present and experimentally demonstrate a protocol
            for measuring the second-order Rényi entropy based on statistical correlations
            between randomized measurements. Our experiments, carried out with a trapped-ion
            quantum simulator with partition sizes of up to 10 qubits,
            prove the overall coherent character of the system dynamics and
            reveal the growth of entanglement between its parts,
            in both the absence and presence of disorder.
            Our protocol represents a universal tool for probing and
            characterizing engineered quantum systems in the laboratory,
            which is applicable to arbitrary quantum states of up to
            several tens of qubits.}}

    Args:
        shots (int):
            Shots of the counts.
        counts (list[dict[str, int]]):
            Counts from randomized measurement results.
        degree (Optional[Union[tuple[int, int], int]]):
            The range of partition.
        measure (Optional[tuple[int, int]], optional):
            The range that implemented the measuring gate.
            If not specified, then use all qubits.
            This will affect the range of partition
            when you not implement the measuring gate on all qubit.
            Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            Backend for the post-processing.
            Defaults to DEFAULT_PROCESS_BACKEND.
        workers_num (Optional[int], optional):
            Number of multi-processing workers, it will be ignored if backend is Rust.
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts by `os.cpu_count()`.
            This only works for Python and Cython backend.
            Defaults to None.
        pbar (Optional[tqdm.tqdm], optional):
            The progress bar API, you can use put a :cls:`tqdm` object here.
            This function will update the progress bar description.
            Defaults to None.

    Returns:
        RandomizedEntangledEntropyComplex:
            A dictionary contains purity, entropy,
            a list of each overlap, puritySD, degree,
            actual measure range, bitstring range and more.
    """

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(f"Calculate specific degree {degree}.")
    (
        purity_cell_dict,
        bitstring_range,
        measure_range,
        _msg,
        taken,
    ) = entangled_entropy_core(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        backend=backend,
        multiprocess_pool_size=workers_num,
    )
    purity_cell_list: list[Union[float, np.float64]] = list(purity_cell_dict.values())

    # pylance cannot recognize the type
    purity: np.float64 = np.mean(purity_cell_list, dtype=np.float64)  # type: ignore
    purity_sd: np.float64 = np.std(purity_cell_list, dtype=np.float64)  # type: ignore
    entropy = -np.log2(purity, dtype=np.float64)
    entropy_sd = purity_sd / np.log(2) / purity

    quantity: RandomizedEntangledEntropyComplex = {
        "purity": purity,
        "entropy": entropy,
        "purityCells": purity_cell_dict,
        "puritySD": purity_sd,
        "entropySD": entropy_sd,
        "degree": degree,
        "measureActually": measure_range,
        "bitStringRange": bitstring_range,
        "countsNum": len(counts),
        "takingTime": taken,
    }

    return quantity


def randomized_entangled_entropy_mitigated_deprecated(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Optional[tuple[int, int]] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    workers_num: Optional[int] = None,
    existed_all_system: Optional[ExistingAllSystemSource] = None,
    pbar: Optional[tqdm.tqdm] = None,
) -> RandomizedEntangledEntropyMitigatedComplex:
    """Calculate entangled entropy with depolarizing error mitigation.
    The entropy we compute is the Second Order Rényi Entropy.

    .. note::
        - Probing Rényi entanglement entropy via randomized measurements -
        Tiff Brydges, Andreas Elben, Petar Jurcevic, Benoît Vermersch,
        Christine Maier, Ben P. Lanyon, Peter Zoller, Rainer Blatt ,and Christian F. Roos ,
        [doi:10.1126/science.aau4963](
            https://www.science.org/doi/abs/10.1126/science.aau4963)

        - Simple mitigation of global depolarizing errors in quantum simulations -
        Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self,
        Christopher and Kim, M. S. and Knolle, Johannes,
        [PhysRevE.104.035309](
            https://link.aps.org/doi/10.1103/PhysRevE.104.035309)

    .. code-block:: bibtex

        @article{doi:10.1126/science.aau4963,
            author = {Tiff Brydges  and Andreas Elben  and Petar Jurcevic
                and Benoît Vermersch  and Christine Maier  and Ben P. Lanyon
                and Peter Zoller  and Rainer Blatt  and Christian F. Roos },
            title = {Probing Rényi entanglement entropy via randomized measurements},
            journal = {Science},
            volume = {364},
            number = {6437},
            pages = {260-263},
            year = {2019},
            doi = {10.1126/science.aau4963},
            URL = {https://www.science.org/doi/abs/10.1126/science.aau4963},
            eprint = {https://www.science.org/doi/pdf/10.1126/science.aau4963},
            abstract = {Quantum systems are predicted to be better at information
            processing than their classical counterparts, and quantum entanglement
            is key to this superior performance. But how does one gauge the degree
            of entanglement in a system? Brydges et al. monitored the build-up of
            the so-called Rényi entropy in a chain of up to 10 trapped calcium ions,
            each of which encoded a qubit. As the system evolved,
            interactions caused entanglement between the chain and the rest of
            the system to grow, which was reflected in the growth of
            the Rényi entropy. Science, this issue p. 260 The buildup of entropy
            in an ion chain reflects a growing entanglement between the chain
            and its complement. Entanglement is a key feature of many-body quantum systems.
            Measuring the entropy of different partitions of a quantum system
            provides a way to probe its entanglement structure.
            Here, we present and experimentally demonstrate a protocol
            for measuring the second-order Rényi entropy based on statistical correlations
            between randomized measurements. Our experiments, carried out with a trapped-ion
            quantum simulator with partition sizes of up to 10 qubits,
            prove the overall coherent character of the system dynamics and
            reveal the growth of entanglement between its parts,
            in both the absence and presence of disorder.
            Our protocol represents a universal tool for probing and
            characterizing engineered quantum systems in the laboratory,
            which is applicable to arbitrary quantum states of up to
            several tens of qubits.}}

            @article{PhysRevE.104.035309,
                title = {Simple mitigation of global depolarizing errors in quantum simulations},
                author = {Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self,
                Christopher and Kim, M. S. and Knolle, Johannes},
                journal = {Phys. Rev. E},
                volume = {104},
                issue = {3},
                pages = {035309},
                numpages = {8},
                year = {2021},
                month = {Sep},
                publisher = {American Physical Society},
                doi = {10.1103/PhysRevE.104.035309},
                url = {https://link.aps.org/doi/10.1103/PhysRevE.104.035309}
            }

    Args:
        shots (int):
            Shots of the counts.
        counts (list[dict[str, int]]):
            Counts from randomized measurement results.
        degree (Optional[Union[tuple[int, int], int]]):
            The range of partition.
        measure (Optional[tuple[int, int]], optional):
            The range that implemented the measuring gate.
            If not specified, then use all qubits.
            This will affect the range of partition
            when you not implement the measuring gate on all qubit.
            Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            Backend for the post-processing.
            Defaults to DEFAULT_PROCESS_BACKEND.
        workers_num (Optional[int], optional):
            Number of multi-processing workers, it will be ignored if backend is Rust.
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts by `os.cpu_count()`.
            This only works for Python and Cython backend.
            Defaults to None.
        existed_all_system (Optional[ExistingAllSystemSource], optional):
            Existing all system source.
            If there is known all system result,
            then you can put it here to save a lot of time on calculating all system
            for not matter what partition you are using,
            their all system result is the same.
            All system source should contain
            `purityCellsAllSys`, `bitStringRange`, `measureActually`, `source` for its name.
            This can save a lot of time
            Defaults to None.
        pbar (Optional[tqdm.tqdm], optional):
            The progress bar API, you can use put a :cls:`tqdm` object here.
            This function will update the progress bar description.
            Defaults to None.

    Returns:
        RandomizedEntangledEntropyMitigatedComplex: A dictionary contains
            purity, entropy, a list of each overlap, puritySD,
            purity of all system, entropy of all system,
            a list of each overlap in all system, puritySD of all system,
            degree, actual measure range, actual measure range in all system, bitstring range.
    """
    null_counts = [i for i, c in enumerate(counts) if len(c) == 0]
    if len(null_counts) > 0:
        return {
            # target system
            "purity": np.nan,
            "entropy": np.nan,
            "purityCells": {},
            "puritySD": np.nan,
            "entropySD": np.nan,
            "bitStringRange": (0, 0),
            # all system
            "allSystemSource": "Null counts exist, no measure.",
            "purityAllSys": np.nan,
            "entropyAllSys": np.nan,
            "purityCellsAllSys": {},
            "puritySDAllSys": np.nan,
            "entropySDAllSys": np.nan,
            "bitsStringRangeAllSys": (0, 0),
            # mitigated
            "errorRate": np.nan,
            "mitigatedPurity": np.nan,
            "mitigatedEntropy": np.nan,
            # info
            "degree": degree,
            "num_qubits": 0,
            "measure": ("The following is the index of null counts.", null_counts),
            "measureActually": (0, 0),
            "measureActuallyAllSys": (0, 0),
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
    purity_cell_list: list[Union[float, np.float64]] = list(purity_cell_dict.values())

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
        purity_cell_list_allsys: list[Union[float, np.float64]] = list(
            purity_cell_dict_allsys.values()
        )  # type: ignore
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
        pbar.set_description_str(f"Preparing error mitigation of {bitstring_range} on {measure}")

    # pylance cannot recognize the type
    purity: np.float64 = np.mean(purity_cell_list, dtype=np.float64)  # type: ignore
    purity_allsys: np.float64 = np.mean(purity_cell_list_allsys, dtype=np.float64)  # type: ignore
    purity_sd: np.float64 = np.std(purity_cell_list, dtype=np.float64)  # type: ignore
    purity_sd_allsys: np.float64 = np.std(purity_cell_list_allsys, dtype=np.float64)  # type: ignore

    entropy: np.float64 = -np.log2(purity, dtype=np.float64)
    entropy_sd: np.float64 = purity_sd / np.log(2) / purity
    entropy_allsys: np.float64 = -np.log2(purity_allsys, dtype=np.float64)
    entropy_sd_allsys: np.float64 = purity_sd_allsys / np.log(2) / purity_allsys

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

    quantity: RandomizedEntangledEntropyMitigatedComplex = {
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
