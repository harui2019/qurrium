"""
===========================================================
Second Renyi Entropy - Randomized Measurement 
(:mod:`qurry.qurrent.randomized_measure`)
===========================================================

"""

from typing import Union, Optional, NamedTuple, Iterable
import tqdm

from .analysis import EntropyRandomizedAnalysis
from ...qurrium.experiment import ExperimentPrototype
from ...process.randomized_measure.entangled_entropy import (
    RandomizedEntangledEntropyMitigatedComplex,
    randomized_entangled_entropy_mitigated,
    ExistingAllSystemSource,
)
from ...process.randomized_measure.entropy_core import (
    PostProcessingBackendLabel,
    DEFAULT_PROCESS_BACKEND,
)
from ...tools import qurry_progressbar, DEFAULT_POOL_SIZE


def _randomized_entangled_entropy_complex(
    shots: int,
    counts: list[dict[str, int]],
    degree: Optional[Union[tuple[int, int], int]],
    measure: Optional[tuple[int, int]] = None,
    all_system_source: Optional[EntropyRandomizedAnalysis] = None,
    backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    workers_num: Optional[int] = None,
    pbar: Optional[tqdm.tqdm] = None,
) -> RandomizedEntangledEntropyMitigatedComplex:
    """Inner wrapper"""

    if all_system_source is not None:
        source = str(all_system_source.header)
        assert (
            all_system_source.content.purityCellsAllSys is not None
        ), f"purityCellsAllSys of {source} is None"
        assert (
            all_system_source.content.bitStringRange is not None
        ), f"bitStringRange of {source} is None"
        assert (
            all_system_source.content.measureActually is not None
        ), f"measureActually of {source} is None"

        existed_all_system: Optional[ExistingAllSystemSource] = {
            "bitStringRange": all_system_source.content.bitStringRange,
            "measureActually": all_system_source.content.measureActually,
            "purityCellsAllSys": all_system_source.content.purityCellsAllSys,
            "source": source,
        }
    else:
        existed_all_system = None

    return randomized_entangled_entropy_mitigated(
        shots=shots,
        counts=counts,
        degree=degree,
        measure=measure,
        backend=backend,
        workers_num=workers_num,
        existed_all_system=existed_all_system,
        pbar=pbar,
    )


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
        counts_used: Optional[Iterable[int]] = None,
        workers_num: Optional[int] = None,
        independent_all_system: bool = False,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> EntropyRandomizedAnalysis:
        """Calculate entangled entropy with more information combined.

        Args:
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            counts_used (Optional[Iterable[int]], optional):
                The index of the counts used.
                If not specified, then use all counts.
                Defaults to None.
            workers_num (Optional[int], optional):
                Number of multi-processing workers,
                if sets to 1, then disable to using multi-processing;
                if not specified, then use the number of all cpu counts - 2 by `cpu_count() - 2`.
                Defaults to None.
            independent_all_system (bool, optional):
                If True, then calculate the all system independently.
                Otherwise, use the existed all system source with same `count_used`.
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
        if isinstance(counts_used, Iterable):
            if max(counts_used) >= len(self.afterwards.counts):
                raise ValueError(
                    "counts_used should be less than "
                    f"{len(self.afterwards.counts)}, but get {max(counts_used)}."
                )
            counts = [self.afterwards.counts[i] for i in counts_used]
        else:
            if counts_used is not None:
                raise ValueError(f"counts_used should be Iterable, but get {type(counts_used)}.")
            counts = self.afterwards.counts

        available_all_system_source = [
            k
            for k, v in self.reports.items()
            if (v.content.allSystemSource == "independent" and v.content.counts_used == counts_used)
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
            counts_used=counts_used,
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
    ) -> RandomizedEntangledEntropyMitigatedComplex:
        """Calculate entangled entropy.

        - Which entropy:

            The entropy we compute is the Second Order Rényi Entropy.

        - Reference:

            Probing Rényi entanglement entropy via randomized measurements -
            Tiff Brydges, Andreas Elben, Petar Jurcevic, Benoît Vermersch,
            Christine Maier, Ben P. Lanyon, Peter Zoller, Rainer Blatt ,and Christian F. Roos ,
            [doi:10.1126/science.aau4963](
                https://www.science.org/doi/abs/10.1126/science.aau4963)

            Simple mitigation of global depolarizing errors in quantum simulations -
            Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self,
            Christopher and Kim, M. S. and Knolle, Johannes,
            [PhysRevE.104.035309](
                https://link.aps.org/doi/10.1103/PhysRevE.104.035309)

        - `bibtex`:

        ```bibtex
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
        ```

        ```bibtex
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

        return _randomized_entangled_entropy_complex(
            shots=shots,
            counts=counts,
            degree=degree,
            measure=measure,
            all_system_source=all_system_source,
            backend=backend,
            workers_num=workers_num,
            pbar=pbar,
        )
