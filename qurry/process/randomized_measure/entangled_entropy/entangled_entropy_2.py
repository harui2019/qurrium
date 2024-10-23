"""
=========================================================================================
Postprocessing - Randomized Measure - Entangled Entropy - Entangled Entropy 2
(:mod:`qurry.process.randomized_measure.entangled_entropy.entangled_entropy_2`)
=========================================================================================

This version introduces another way to process subsystems.

"""

from typing import Union, Optional
import warnings
import numpy as np
import tqdm

from .entropy_core_2 import entangled_entropy_core_2, DEFAULT_PROCESS_BACKEND
from .container import (
    EntangledEntropyResult,
    EntangledEntropyResultMitigated,
    ExistedAllSystemInfo,
)
from .error_mitigation import depolarizing_error_mitgation
from ...availability import PostProcessingBackendLabel


def randomized_entangled_entropy(
    shots: int,
    counts: list[dict[str, int]],
    selected_classical_registers: Optional[list[int]] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    pbar: Optional[tqdm.tqdm] = None,
) -> EntangledEntropyResult:
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
            Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        selected_classical_registers (Optional[list[int]], optional):
            The list of **the index of the selected_classical_registers**.
        backend (ExistingProcessBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
        pbar (Optional[tqdm.tqdm], optional):
            The progress bar API, you can use put a :cls:`tqdm` object here.
            This function will update the progress bar description.
            Defaults to None.

    Returns:
        EntangledEntropyReturn:
            A dictionary contains purity, entropy, a dictionary of each purity cell,
            entropySD, puritySD, num_classical_registers, classical_registers,
            classical_registers_actually, counts_num, taking_time.
    """

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(
            f"Calculate selected classical registers: {selected_classical_registers}."
        )
    (
        purity_cell_dict,
        selected_classical_registers_actual,
        _msg,
        taken,
    ) = entangled_entropy_core_2(
        shots=shots,
        counts=counts,
        selected_classical_registers=selected_classical_registers,
        backend=backend,
    )
    purity_cell_list: list[Union[float, np.float64]] = list(purity_cell_dict.values())

    # pylance cannot recognize the type
    purity: np.float64 = np.mean(purity_cell_list, dtype=np.float64)  # type: ignore
    purity_sd: np.float64 = np.std(purity_cell_list, dtype=np.float64)  # type: ignore
    entropy = -np.log2(purity, dtype=np.float64)
    entropy_sd = purity_sd / np.log(2) / purity

    num_classical_registers = len(list(counts[0].keys())[0])

    quantity: EntangledEntropyResult = {
        "purity": purity,
        "entropy": entropy,
        "puritySD": purity_sd,
        "entropySD": entropy_sd,
        "purityCells": purity_cell_dict,
        # new added
        "num_classical_registers": num_classical_registers,
        "classical_registers": selected_classical_registers,
        "classical_registers_actually": selected_classical_registers_actual,
        # refactored
        "counts_num": len(counts),
        "taking_time": taken,
    }

    return quantity


def preparing_all_system(
    existed_all_system: Optional[ExistedAllSystemInfo],
    shots: int,
    counts: list[dict[str, int]],
    backend: PostProcessingBackendLabel,
    pbar: Optional[tqdm.tqdm] = None,
) -> ExistedAllSystemInfo:
    """Prepare all system for the entangled entropy calculation.

    Args:
        existed_all_system (Optional[ExistedAllSystemInfo]):
            Existing all system source.
            If there is known all system result,
            then you can put it here to save a lot of time on calculating all system
            for no matter what partition you are using,
            their all system result is the same.
            This can save a lot of time
            Defaults to None.
        shots (int):
            Shots of the counts.
        counts (list[dict[str, int]]):
            Counts from randomized measurement results.
        backend (PostProcessingBackendLabel):
            Backend for the process.
        pbar (Optional[tqdm.tqdm], optional):
            The progress bar API, you can use put a :cls:`tqdm` object here.
            This function will update the progress bar description.
            Defaults to None.

    Returns:
        ExistedAllSystemInfo:
            The all system information.
    """

    if isinstance(existed_all_system, ExistedAllSystemInfo):
        if isinstance(pbar, tqdm.tqdm):
            pbar.set_description_str(
                f"Using existing all system from '{existed_all_system.source}'"
            )
        return existed_all_system
    if existed_all_system is not None:
        warnings.warn(
            "The existed_all_system is not valid, it should be None or ExistedAllSystemInfo.",
            RuntimeWarning,
        )

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(f"Calculate all system by {backend}.")
    (
        purity_cell_dict_allsys,
        selected_qubits_sorted_allsys,
        _msg_allsys,
        taken_allsys,
    ) = entangled_entropy_core_2(
        shots=shots,
        counts=counts,
        selected_classical_registers=None,
        backend=backend,
    )

    purity_all_sys = np.mean(list(purity_cell_dict_allsys.values()), dtype=np.float64)
    purity_sd_all_sys = np.std(list(purity_cell_dict_allsys.values()), dtype=np.float64)
    entropy_all_sys = -np.log2(purity_all_sys, dtype=np.float64)
    entropy_sd_all_sys = purity_sd_all_sys / np.log(2) / purity_all_sys

    num_classical_registers_all_sys = len(list(counts[0].keys())[0])

    return ExistedAllSystemInfo(
        source="independent",
        purityAllSys=purity_all_sys,
        entropyAllSys=entropy_all_sys,
        puritySDAllSys=purity_sd_all_sys,
        entropySDAllSys=entropy_sd_all_sys,
        purityCellsAllSys=purity_cell_dict_allsys,
        num_classical_registers_all_sys=num_classical_registers_all_sys,
        classical_registers_all_sys=None,
        classical_registers_actually_all_sys=selected_qubits_sorted_allsys,
        taking_time_all_sys=taken_allsys,
    )


def randomized_entangled_entropy_mitigated(
    shots: int,
    counts: list[dict[str, int]],
    selected_classical_registers: Optional[list[int]] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    existed_all_system: Optional[ExistedAllSystemInfo] = None,
    pbar: Optional[tqdm.tqdm] = None,
) -> EntangledEntropyResultMitigated:
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
        selected_classical_registers (Optional[list[int]], optional):
            The list of **the index of the selected_classical_registers**.
        backend (ExistingProcessBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
        existed_all_system (Optional[ExistedAllSystemInfo], optional):
            Existing all system source.
            If there is known all system result,
            then you can put it here to save a lot of time on calculating all system
            for no matter what partition you are using,
            their all system result is the same.
            This can save a lot of time
            Defaults to None.
        pbar (Optional[tqdm.tqdm], optional):
            The progress bar API, you can use put a :cls:`tqdm` object here.
            This function will update the progress bar description.
            Defaults to None.

    Returns:
        EntangledEntropyResultMitigated: A dictionary contains
            purity, entropy, a dictionary of each purity cell,
            entropySD, puritySD, num_classical_registers, classical_registers,
            classical_registers_actually, counts_num, taking_time,
            purityAllSys, entropyAllSys, puritySDAllSys, entropySDAllSys,
            num_classical_registers_all_sys, classical_registers_all_sys,
            classical_registers_actually_all_sys, errorRate, mitigatedPurity, mitigatedEntropy.
    """
    null_counts = [i for i, c in enumerate(counts) if len(c) == 0]
    if len(null_counts) > 0:
        return {
            # target system
            "purity": np.nan,
            "entropy": np.nan,
            "puritySD": np.nan,
            "entropySD": np.nan,
            "purityCells": {},
            # all system
            "all_system_source": "null_counts",
            "purityAllSys": np.nan,
            "entropyAllSys": np.nan,
            "puritySDAllSys": np.nan,
            "entropySDAllSys": np.nan,
            "purityCellsAllSys": {},
            # new systems info
            "num_classical_registers": 0,
            "num_classical_registers_all_sys": 0,
            "classical_registers": selected_classical_registers,
            "classical_registers_actually": [],
            "classical_registers_all_sys": None,
            "classical_registers_actually_all_sys": [],
            # mitigated
            "errorRate": np.nan,
            "mitigatedPurity": np.nan,
            "mitigatedEntropy": np.nan,
            # refactored systems info
            "counts_num": len(counts),
            "taking_time": 0,
            "taking_time_all_sys": 0,
        }

    num_qubits = len(list(counts[0].keys())[0])

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(
            f"Calculate selected classical registers: {selected_classical_registers}."
        )

    (
        purity_cell_dict,
        selected_qubits_sorted,
        _msg,
        taken,
    ) = entangled_entropy_core_2(
        shots=shots,
        counts=counts,
        selected_classical_registers=selected_classical_registers,
        backend=backend,
    )
    purity_cell_list: list[Union[float, np.float64]] = list(purity_cell_dict.values())

    all_system = preparing_all_system(
        existed_all_system=existed_all_system,
        shots=shots,
        counts=counts,
        backend=backend,
        pbar=pbar,
    )
    num_classical_registers = len(list(counts[0].keys())[0])

    assert num_classical_registers == all_system.num_classical_registers_all_sys, (
        "The number of classical registers is not matched."
        + " num_classical_registers != num_classical_registers_all_sys:"
        + f" {num_classical_registers} != {all_system.num_classical_registers_all_sys}"
    )

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(
            f"Preparing error mitigation of selected qubits: {selected_qubits_sorted}"
        )

    # pylance cannot recognize the type
    purity: np.float64 = np.mean(purity_cell_list, dtype=np.float64)  # type: ignore
    purity_sd: np.float64 = np.std(purity_cell_list, dtype=np.float64)  # type: ignore
    entropy: np.float64 = -np.log2(purity, dtype=np.float64)
    entropy_sd: np.float64 = purity_sd / np.log(2) / purity

    error_mitgation_info = depolarizing_error_mitgation(
        meas_system=purity,
        all_system=all_system.purityAllSys,
        n_a=len(selected_qubits_sorted),
        system_size=num_qubits,
    )

    return {
        # target system
        "purity": purity,
        "entropy": entropy,
        "puritySD": purity_sd,
        "entropySD": entropy_sd,
        "purityCells": purity_cell_dict,
        # all system
        "all_system_source": all_system.source,
        "purityAllSys": all_system.purityAllSys,
        "entropyAllSys": all_system.entropyAllSys,
        "puritySDAllSys": all_system.puritySDAllSys,
        "entropySDAllSys": all_system.entropySDAllSys,
        "purityCellsAllSys": all_system.purityCellsAllSys,
        # new systems info
        "num_classical_registers": num_classical_registers,
        "num_classical_registers_all_sys": all_system.num_classical_registers_all_sys,
        "classical_registers": selected_classical_registers,
        "classical_registers_actually": selected_qubits_sorted,
        "classical_registers_all_sys": all_system.classical_registers_all_sys,
        "classical_registers_actually_all_sys": all_system.classical_registers_actually_all_sys,
        # mitigated
        "errorRate": error_mitgation_info["errorRate"],
        "mitigatedPurity": error_mitgation_info["mitigatedPurity"],
        "mitigatedEntropy": error_mitgation_info["mitigatedEntropy"],
        # refactored systems info
        "counts_num": len(counts),
        "taking_time": taken,
        "taking_time_all_sys": all_system.taking_time_all_sys,
    }
