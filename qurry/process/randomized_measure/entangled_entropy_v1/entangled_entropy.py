"""Post Processing - Randomized Measure - Entangled Entropy V1 - Entangled Entropy Deprecated
(:mod:`qurry.process.randomized_measure.entangled_entropy_v1.entangled_entropy`)

"""

import numpy as np
import tqdm

from .entropy_core import entangled_entropy_core, DEFAULT_PROCESS_BACKEND
from .container import TargetSystemResultV1, AllSystemResultV1, isvalid_all_system_result_v1
from ...utils import depolarizing_error_mitgation, MitigatedResult
from ...availability import PostProcessingBackendLabel


def randomized_entangled_entropy_v1(
    shots: int,
    counts: list[dict[str, int]],
    degree: tuple[int, int] | int | None,
    measure: tuple[int, int] | None = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    workers_num: int | None = None,
    pbar: tqdm.tqdm | None = None,
) -> TargetSystemResultV1:
    """Calculate entangled entropy.
    The entropy we compute is the Second Order Rényi Entropy.

    Reference:
        - Randomized Measure - Entangled Entropy
            -   Probing Rényi entanglement entropy via randomized measurements -
                Tiff Brydges, Andreas Elben, Petar Jurcevic, Benoît Vermersch,
                Christine Maier, Ben P. Lanyon, Peter Zoller, Rainer Blatt ,and Christian F. Roos,
                `doi:10.1126/science.aau4963
                <https://www.science.org/doi/abs/10.1126/science.aau4963>`_

            -   Statistical correlations between locally randomized measurements:
                A toolbox for probing entanglement in many-body quantum states -
                A. Elben, B. Vermersch, C. F. Roos, and P. Zoller,
                `PhysRevA.99.052323 <https://doi.org/10.1103/PhysRevA.99.052323>`_

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
                several tens of qubits.}
            }

            @article{PhysRevA.99.052323,
                title = {
                    Statistical correlations between locally randomized measurements:
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

    Args:
        shots (int):
            Shots of the counts.
        counts (list[dict[str, int]]):
            Counts from randomized measurement results.
        degree (tuple[int, int] | int | None):
            The range of partition.
        measure (tuple[int, int] | None, optional):
            The range that implemented the measuring gate.
            If not specified, then use all qubits.
            This will affect the range of partition
            when you not implement the measuring gate on all qubit.
            Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            Backend for the post-processing.
            Defaults to DEFAULT_PROCESS_BACKEND.
        workers_num (int | None, optional):
            Number of multi-processing workers, it will be ignored if backend is Rust.
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts by `os.cpu_count()`.
            This only works for Python and Cython backend.
            Defaults to None.
        pbar (tqdm.tqdm | None, optional):
            The progress bar API,
            you can use put a `tqdm.tqdm <https://tqdm.github.io/>` object here.
            This function will update the progress bar description.
            Defaults to None.

    Returns:
        A dictionary contains purity, entropy,
        a list of each overlap, puritySD, degree,
        actual measure range, bitstring range and more.
    """

    null_counts = [i for i, c in enumerate(counts) if len(c) == 0]
    if len(null_counts) > 0:
        raise ValueError(
            "The counts contain null counts at index: "
            + f"{null_counts}. Cannot perform entangled entropy calculation."
        )

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
    purity_cell_list = list(purity_cell_dict.values())

    # pylance cannot recognize the type
    purity: np.float64 = np.mean(purity_cell_list, dtype=np.float64)  # type: ignore
    purity_sd: np.float64 = np.std(purity_cell_list, dtype=np.float64)  # type: ignore
    entropy = -np.log2(purity, dtype=np.float64)
    entropy_sd = purity_sd / np.log(2) / purity

    num_qubits = len(list(counts[0].keys())[0])

    quantity: TargetSystemResultV1 = {
        "purity": purity,
        "entropy": entropy,
        "puritySD": purity_sd,
        "entropySD": entropy_sd,
        "purityCells": purity_cell_dict,
        "bitStringRange": bitstring_range,
        "degree": degree,
        "measureActually": measure_range,
        "num_qubits": num_qubits,
        "countsNum": len(counts),
        "takingTime": taken,
    }

    return quantity


def preparing_all_system(
    shots: int,
    counts: list[dict[str, int]],
    measure: tuple[int, int] | None = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    workers_num: int | None = None,
    existed_all_system: AllSystemResultV1 | None = None,
) -> AllSystemResultV1:
    """Prepare the all system source for entangled entropy calculation.

    Args:
        shots (int):
            Shots of the counts.
        counts (list[dict[str, int]]):
            Counts from randomized measurement results.
        measure (tuple[int, int] | None, optional):
            The range that implemented the measuring gate.
            If not specified, then use all qubits.
            This will affect the range of partition
            when you not implement the measuring gate on all qubit.
            Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            Backend for the post-processing.
            Defaults to DEFAULT_PROCESS_BACKEND.
        workers_num (int | None, optional):
            Number of multi-processing workers, it will be ignored if backend is Rust.
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts by `os.cpu_count()`.
            This only works for Python and Cython backend.
            Defaults to None.
        existed_all_system (AllSystemResultV1 | None, optional):
            Existing all system source.
            If there is known all system result,
            then you can put it here to save a lot of time on calculating all system
            for not matter what partition you are using,
            their all system result is the same.
            All system source should contain
            `purityCellsAllSys`, `bitStringRange`, `measureActually`, `source` for its name.
            This can save a lot of time
            Defaults to None.

    Returns:
        The result of all system for entangled entropy calculation.
    """
    if existed_all_system is not None:
        isvalid_all_system_result_v1(existed_all_system)
        return existed_all_system

    target_system_result_v1_allsys = randomized_entangled_entropy_v1(
        shots=shots,
        counts=counts,
        degree=None,
        measure=measure,
        backend=backend,
        workers_num=workers_num,
    )

    return AllSystemResultV1(**target_system_result_v1_allsys, allSystemSource="independent")


def randomized_entangled_entropy_mitigated_v1(
    shots: int,
    counts: list[dict[str, int]],
    degree: tuple[int, int] | int | None,
    measure: tuple[int, int] | None = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    workers_num: int | None = None,
    existed_all_system: AllSystemResultV1 | None = None,
) -> tuple[TargetSystemResultV1, AllSystemResultV1, MitigatedResult]:
    """Calculate entangled entropy with depolarizing error mitigation.
    The entropy we compute is the Second Order Rényi Entropy.

    Reference:
        - Randomized Measure - Entangled Entropy
            -   Probing Rényi entanglement entropy via randomized measurements -
                Tiff Brydges, Andreas Elben, Petar Jurcevic, Benoît Vermersch,
                Christine Maier, Ben P. Lanyon, Peter Zoller, Rainer Blatt ,and Christian F. Roos,
                `doi:10.1126/science.aau4963
                <https://www.science.org/doi/abs/10.1126/science.aau4963>`_

            -   Statistical correlations between locally randomized measurements:
                A toolbox for probing entanglement in many-body quantum states -
                A. Elben, B. Vermersch, C. F. Roos, and P. Zoller,
                `PhysRevA.99.052323 <https://doi.org/10.1103/PhysRevA.99.052323>`_

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
                several tens of qubits.}
            }

            @article{PhysRevA.99.052323,
                title = {
                    Statistical correlations between locally randomized measurements:
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

        - Error Mitigation
            -   Simple mitigation of global depolarizing errors in quantum simulations -
                Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self,
                Christopher and Kim, M. S. and Knolle, Johannes,
                `PhysRevE.104.035309 <https://link.aps.org/doi/10.1103/PhysRevE.104.035309>`_

        .. code-block:: bibtex

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
        degree (tuple[int, int] | int | None):
            The range of partition.
        measure (tuple[int, int] | None, optional):
            The range that implemented the measuring gate.
            If not specified, then use all qubits.
            This will affect the range of partition
            when you not implement the measuring gate on all qubit.
            Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            Backend for the post-processing.
            Defaults to DEFAULT_PROCESS_BACKEND.
        workers_num (int | None, optional):
            Number of multi-processing workers, it will be ignored if backend is Rust.
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts by `os.cpu_count()`.
            This only works for Python and Cython backend.
            Defaults to None.
        existed_all_system (AllSystemResultV1 | None, optional):
            Existing all system source.
            If there is known all system result,
            then you can put it here to save a lot of time on calculating all system
            for not matter what partition you are using,
            their all system result is the same.
            All system source should contain
            `purityCellsAllSys`, `bitStringRange`, `measureActually`, `source` for its name.
            This can save a lot of time
            Defaults to None.

    Returns:
        A tuple of three elements:
        - TargetSystemResultV1:
            The result of target system for entangled entropy calculation.
        - AllSystemResultV1:
            The result of all system for entangled entropy calculation.
        - MitigatedResult:
            The result after depolarizing error mitigation.
    """
    target_system_result_v1 = randomized_entangled_entropy_v1(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        backend=backend,
        workers_num=workers_num,
    )
    all_system_result_v1 = preparing_all_system(
        shots=shots,
        counts=counts,
        measure=measure,
        backend=backend,
        workers_num=workers_num,
        existed_all_system=existed_all_system,
    )

    num_qubits = len(list(counts[0].keys())[0])
    if degree is None:
        degree = num_qubits
    subsystem = max(degree) - min(degree) if isinstance(degree, tuple) else degree

    mitigated_result = depolarizing_error_mitgation(
        meas_system=target_system_result_v1["purity"],
        all_system=all_system_result_v1["purity"],
        subsystem_size=subsystem,
        system_size=num_qubits,
    )

    return target_system_result_v1, all_system_result_v1, mitigated_result
