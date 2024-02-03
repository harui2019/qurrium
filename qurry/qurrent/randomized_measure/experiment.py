"""
===========================================================
Second Renyi Entropy - Randomized Measurement 
(:mod:`qurry.qurrent.randomized_measure`)
===========================================================

"""

from typing import Union, Optional, NamedTuple
import numpy as np
import tqdm

from .analysis import EntropyRandomizedAnalysis
from ...qurrium.experiment import ExperimentPrototype
from ...process.randomized_measure.entangled_entropy import (
    entangled_entropy_core,
    RandomizedEntangledEntropyComplex,
)
from ...process.randomized_measure.entropy_core import (
    PostProcessingBackendLabel,
    DEFAULT_PROCESS_BACKEND,
)
from ...process.randomized_measure.error_mitigation import depolarizing_error_mitgation
from ...tools import qurry_progressbar, DEFAULT_POOL_SIZE


def randomized_entangled_entropy_complex(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Optional[tuple[int, int]] = None,
    all_system_source: Optional[EntropyRandomizedAnalysis] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    workers_num: Optional[int] = None,
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
        all_system_source (Optional['EntropyRandomizedAnalysis'], optional):
            The source of the all system. Defaults to None.
        backend (PostProcessingBackendLabel, optional):
            Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
        workers_num (Optional[int], optional):
            Number of multi-processing workers, it will be ignored if backend is Rust.
            if sets to 1, then disable to using multi-processing;
            if not specified, then use the number of all cpu counts by `os.cpu_count()`.
            Defaults to None.
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

    if all_system_source is None:
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
        purity_cell_list_allsys: Union[list[float], list[np.float64]] = list(
            purity_cell_dict_allsys.values()
        )  # type: ignore
        source = "independent"
    else:
        content: EntropyRandomizedAnalysis.AnalysisContent = all_system_source.content
        source = str(all_system_source.header)
        if isinstance(pbar, tqdm.tqdm):
            pbar.set_description_str(f"Using existing all system from '{source}'")
        purity_cell_dict_allsys = content.purityCellsAllSys
        assert (
            purity_cell_dict_allsys is not None
        ), "all_system_source.content.purityCells is None"
        purity_cell_list_allsys = list(purity_cell_dict_allsys.values())
        bitstring_range_allsys = content.bitStringRange
        measure_range_allsys = content.measureActually
        _msg_allsys = f"Use all system from {source}."
        taken_allsys = 0

    if isinstance(pbar, tqdm.tqdm):
        pbar.set_description_str(
            f"Preparing error mitigation of {bitstring_range} on {measure}"
        )

    purity: np.float64 = np.mean(purity_cell_list, dtype=np.float64)
    purity_allsys = np.mean(purity_cell_list_allsys, dtype=np.float64)
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


class EntropyRandomizedArguments(NamedTuple):
    """Arguments for the experiment."""

    exp_name: str = "exps"
    times: int = 100
    measure: Optional[tuple[int, int]] = None
    unitary_loc: Optional[tuple[int, int]] = None
    workers_num: int = DEFAULT_POOL_SIZE


class EntropyRandomizedExperiment(ExperimentPrototype):
    """The instance for the experiment of :cls:`EntropyRandomizedMeasure`."""

    __name__ = "qurrentRandomized.Experiment"
    shortName = "qurrent_haar.exp"

    tqdm_handleable = True
    """The handleable of tqdm."""

    Arguments = EntropyRandomizedArguments
    args: EntropyRandomizedArguments

    analysis_container = EntropyRandomizedAnalysis
    """The container class responding to this QurryV5 class."""

    def analyze(
        self,
        degree: Optional[Union[tuple[int, int], int]] = None,
        workers_num: Optional[int] = None,
        independent_all_system: bool = False,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> EntropyRandomizedAnalysis:
        """Calculate entangled entropy with more information combined.

        Args:
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            workers_num (Optional[int], optional):
                Number of multi-processing workers,
                if sets to 1, then disable to using multi-processing;
                if not specified, then use the number of all cpu counts - 2 by `cpu_count() - 2`.
                Defaults to None.
            independent_all_system (bool, optional):
                If True, then calculate the all system independently.
            backend (PostProcessingBackendLabel, optional):
                Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
            pbar (Optional[tqdm.tqdm], optional): Progress bar. Defaults to None.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy, a list of each overlap, puritySD,
                purity of all system, entropy of all system,
                a list of each overlap in all system, puritySD of all system,
                degree, actual measure range, actual measure range in all system, bitstring range.
        """
        if degree is None:
            raise ValueError("degree should be specified.")

        self.args: EntropyRandomizedExperiment.Arguments
        self.reports: dict[int, EntropyRandomizedAnalysis]
        shots = self.commons.shots
        measure = self.args.measure
        unitary_loc = self.args.unitary_loc
        counts = self.afterwards.counts

        available_all_system_source = [
            k
            for k, v in self.reports.items()
            if v.content.allSystemSource == "independent"
        ]

        if len(available_all_system_source) > 0 and not independent_all_system:
            all_system_source = self.reports[available_all_system_source[-1]]
        else:
            all_system_source = None

        if isinstance(pbar, tqdm.tqdm):
            qs = self.quantities(
                shots=shots,
                counts=counts,
                degree=degree,
                measure=measure,
                all_system_source=all_system_source,
                backend=backend,
                workers_num=workers_num,
                pbar=pbar,
            )

        else:
            pbar_selfhost = qurry_progressbar(
                range(1),
                bar_format="simple",
            )

            with pbar_selfhost as pb_self:
                qs = self.quantities(
                    shots=shots,
                    counts=counts,
                    degree=degree,
                    measure=measure,
                    all_system_source=all_system_source,
                    backend=backend,
                    workers_num=workers_num,
                    pbar=pb_self,
                )
                pb_self.update()

        serial = len(self.reports)
        analysis = self.analysis_container(
            serial=serial,
            shots=shots,
            unitary_loc=unitary_loc,
            **qs,
        )

        self.reports[serial] = analysis
        return analysis

    @classmethod
    def quantities(
        cls,
        shots: Optional[int] = None,
        counts: Optional[list[dict[str, int]]] = None,
        degree: Optional[Union[tuple[int, int], int]] = None,
        measure: Optional[tuple[int, int]] = None,
        all_system_source: Optional["EntropyRandomizedAnalysis"] = None,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        workers_num: Optional[int] = None,
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
            all_system_source (Optional['EntropyRandomizedAnalysis'], optional):
                The source of the all system. Defaults to None.
            backend (PostProcessingBackendLabel, optional):
                Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
            workers_num (Optional[int], optional):
                Number of multi-processing workers, it will be ignored if backend is Rust.
                if sets to 1, then disable to using multi-processing;
                if not specified, then use the number of all cpu counts by `os.cpu_count()`.
                Defaults to None.
            pbar (Optional[tqdm.tqdm], optional): Progress bar. Defaults to None.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy, a list of each overlap, puritySD,
                purity of all system, entropy of all system,
                a list of each overlap in all system, puritySD of all system,
                degree, actual measure range, actual measure range in all system, bitstring range.
        """

        if shots is None or counts is None:
            raise ValueError("shots and counts should be specified.")

        return randomized_entangled_entropy_complex(
            shots=shots,
            counts=counts,
            degree=degree,
            measure=measure,
            all_system_source=all_system_source,
            backend=backend,
            workers_num=workers_num,
            pbar=pbar,
        )
