"""Post Processing - Randomized Measure - Entangled Entropy - Entangled Entropy 2
(:mod:`qurry.process.randomized_measure.entangled_entropy.entangled_entropy_2`)

"""

from collections.abc import Iterable
import numpy as np
import tqdm

from .entropy_core_2 import entangled_entropy_core_2, DEFAULT_PROCESS_BACKEND
from .container import TargetSystemResult, AllSystemResult, isvalid_all_system_result
from ..utils import generate_hash_from_trace_result
from ...utils import (
    depolarizing_error_mitgation,
    MitigatedResult,
    shot_counts_selected_clreg_checker,
)
from ...availability import PostProcessingBackendLabel
from ....tools import current_time


def randomized_entangled_entropy(
    shots: int,
    counts: list[dict[str, int]],
    selected_classical_registers: Iterable[int] | None = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    pbar: tqdm.tqdm | None = None,
) -> TargetSystemResult:
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
            Shots of the experiment on quantum machine.
        counts (list[dict[str, int]]):
            Counts of the experiment on quantum machine.
        selected_classical_registers (Iterable[int] | None, optional):
            The list of **the index of the selected_classical_registers**. Defaults to None.
        backend (ExistingProcessBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
        pbar (tqdm.tqdm | None, optional):
            The progress bar API,
            you can use put a `tqdm.tqdm <https://tqdm.github.io/>` object here.
            This function will update the progress bar description.
            Defaults to None.

    Returns:
        A dictionary contains purity, entropy, a dictionary of each purity cell,
        entropySD, puritySD, num_classical_registers, classical_registers,
        classical_registers_actually, counts_num, taking_time.
    """

    null_counts = [i for i, c in enumerate(counts) if len(c) == 0]
    if len(null_counts) > 0:
        raise ValueError(
            "The counts contain null counts at index: "
            + f"{null_counts}. Cannot perform entangled entropy calculation."
        )

    if pbar is not None:
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
    purity_cell_list = list(purity_cell_dict.values())

    # pylance cannot recognize the type
    purity: np.float64 = np.mean(purity_cell_list, dtype=np.float64)  # type: ignore
    purity_sd: np.float64 = np.std(purity_cell_list, dtype=np.float64)  # type: ignore
    entropy = -np.log2(purity, dtype=np.float64)
    entropy_sd = purity_sd / np.log(2) / purity

    num_classical_registers = len(next(iter(counts[0].keys())))

    return TargetSystemResult(
        purity=purity,
        entropy=entropy,
        purity_sd=purity_sd,
        entropy_sd=entropy_sd,
        purity_cells=purity_cell_dict,
        # new added
        num_classical_registers=num_classical_registers,
        classical_registers=(
            selected_classical_registers
            if selected_classical_registers is None
            else list(selected_classical_registers)
        ),
        classical_registers_actually=selected_classical_registers_actual,
        # refactored
        counts_num=len(counts),
        taking_time=taken,
    )


def preparing_all_system(
    shots: int,
    counts: list[dict[str, int]],
    existed_all_system: AllSystemResult | None = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    pbar: tqdm.tqdm | None = None,
) -> AllSystemResult:
    """Prepare all system for the entangled entropy calculation.

    Args:
        shots (int):
            Shots of the counts.
        counts (list[dict[str, int]]):
            Counts from randomized measurement results.
        existed_all_system (AllSystemResult | None, optional):
            Existing all system source.
            If there is known all system result, then you can put it here
            to save a lot of time on calculating all system for no matter
            what partition you are using, their all system result is the same.
            This can save a lot of time
            Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
        pbar (tqdm.tqdm | None, optional):
            The progress bar API,
            you can use put a `tqdm.tqdm <https://tqdm.github.io/>` object here.
            This function will update the progress bar description.
            Defaults to None.

    Returns:
        ExistedAllSystemInfo:
            The all system information.
    """
    if existed_all_system is not None:
        isvalid_all_system_result(existed_all_system)

        total_system_size, selected_clregs = shot_counts_selected_clreg_checker(
            shots=shots,
            counts=counts,
            selected_classical_registers=None,
        )
        selected_clregs_sorted = sorted(selected_clregs)
        selected_clregs_sorted_existed_all_system = sorted(
            existed_all_system["classical_registers_actually"]
        )
        if total_system_size != len(selected_clregs_sorted_existed_all_system):
            raise ValueError(
                "The number of classical registers is not matched with the existed all system. "
                + "total_system_size != "
                + "len(existed_all_system['classical_registers_actually']): "
                + f"{total_system_size} != {len(selected_clregs_sorted_existed_all_system)}"
            )
        if selected_clregs_sorted != selected_clregs_sorted_existed_all_system:
            raise ValueError(
                "The selected classical registers is not matched with the existed all system. "
                + "selected_classical_registers != "
                + "existed_all_system['classical_registers_actually']: "
                + f"{selected_clregs_sorted} != {selected_clregs_sorted_existed_all_system}"
            )

        existed_all_system["all_system_source"] = (
            "AllSystemResult("
            + f"preparing_datetime={existed_all_system['preparing_datetime']}, "
            + f"result_hash_id={existed_all_system['result_hash_id']})"
        )
        if isinstance(pbar, tqdm.tqdm):
            pbar.set_description_str(
                f"Using existing all system from '{existed_all_system['all_system_source']}'"
            )
        return existed_all_system

    target_obj_all_system = randomized_entangled_entropy(
        shots=shots,
        counts=counts,
        selected_classical_registers=None,
        backend=backend,
        pbar=pbar,
    )

    preparing_datetime = current_time()
    result_hash_id = generate_hash_from_trace_result(
        purity_or_echo=target_obj_all_system["purity"],
        classical_registers_actually=target_obj_all_system["classical_registers_actually"],
        taking_time=target_obj_all_system["taking_time"],
        counts_num=target_obj_all_system["counts_num"],
        shots=shots,
        preparing_datetime=preparing_datetime,
    )
    return AllSystemResult(
        **target_obj_all_system,
        preparing_datetime=preparing_datetime,
        result_hash_id=result_hash_id,
        all_system_source="independent",
    )


def randomized_entangled_entropy_mitigated(
    shots: int,
    counts: list[dict[str, int]],
    selected_classical_registers: Iterable[int] | None = None,
    existed_all_system: AllSystemResult | None = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    pbar: tqdm.tqdm | None = None,
) -> tuple[TargetSystemResult, AllSystemResult, MitigatedResult]:
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
        selected_classical_registers (Iterable[int] | None, optional):
            The list of **the index of the selected_classical_registers**. Defaults to None.
        existed_all_system (AllSystemResult | None, optional):
            Existing all system source.
            If there is known all system result, then you can put it here
            to save a lot of time on calculating all system for no matter
            what partition you are using, their all system result is the same.
            This can save a lot of time
            Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
        pbar (tqdm.tqdm | None, optional):
            The progress bar API,
            you can use put a `tqdm.tqdm <https://tqdm.github.io/>` object here.
            This function will update the progress bar description.
            Defaults to None.

    Returns:
        The target system result, all system result, and mitigated result.
    """

    target_system_result = randomized_entangled_entropy(
        shots=shots,
        counts=counts,
        selected_classical_registers=selected_classical_registers,
        backend=backend,
        pbar=pbar,
    )
    all_system_result = preparing_all_system(
        existed_all_system=existed_all_system,
        shots=shots,
        counts=counts,
        backend=backend,
        pbar=pbar,
    )
    error_mitgation_info = depolarizing_error_mitgation(
        meas_system=target_system_result["purity"],
        all_system=all_system_result["purity"],
        subsystem_size=len(target_system_result["classical_registers_actually"]),
        system_size=len(all_system_result["classical_registers_actually"]),
    )

    return target_system_result, all_system_result, error_mitgation_info
