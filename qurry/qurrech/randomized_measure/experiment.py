"""
===========================================================
Wave Function Overlap - Randomized Measurement Experiment
(:mod:`qurry.qurrech.randomized_measure.experiment`)
===========================================================

"""

from typing import Union, Optional, Hashable, NamedTuple, Iterable
import tqdm

from .analysis import EchoRandomizedAnalysis
from ...qurrium.experiment import ExperimentPrototype
from ...process.randomized_measure.wavefunction_overlap import (
    randomized_overlap_echo,
    PostProcessingBackendLabel,
    DEFAULT_PROCESS_BACKEND,
)
from ...tools import qurry_progressbar, DEFAULT_POOL_SIZE


class EchoRandomizedArguments(NamedTuple):
    """Arguments for the experiment."""

    exp_name: str = "exps"
    wave_key_2: Optional[Hashable] = None
    times: int = 100
    measure: Optional[tuple[int, int]] = None
    unitary_loc: Optional[tuple[int, int]] = None
    workers_num: int = DEFAULT_POOL_SIZE


class EchoRandomizedExperiment(ExperimentPrototype):
    """Randomized measure experiment.

    - Reference:
        - Used in:
            Simple mitigation of global depolarizing errors in quantum simulations -
            Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self,
            Christopher and Kim, M. S. and Knolle, Johannes,
            [PhysRevE.104.035309](https://link.aps.org/doi/10.1103/PhysRevE.104.035309)

        - `bibtex`:

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
    """

    __name__ = "qurrechRandomized.Experiment"
    shortName = "qurrech_haar.exp"

    Arguments = EchoRandomizedArguments
    args: EchoRandomizedArguments

    analysis_container = EchoRandomizedAnalysis
    """The container class responding to this QurryV5 class."""

    def analyze(
        self,
        degree: Optional[Union[tuple[int, int], int]] = None,
        counts_used: Optional[Iterable[int]] = None,
        workers_num: Optional[int] = None,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> EchoRandomizedAnalysis:
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
            raise ValueError("degree must be specified, but get None.")

        self.args: EchoRandomizedExperiment.Arguments
        shots = self.commons.shots
        measure = self.args.measure
        unitary_loc = self.args.unitary_loc
        len_counts = len(self.afterwards.counts)
        assert len_counts % 2 == 0, "The counts should be even."
        len_counts_half = int(len_counts / 2)
        if isinstance(counts_used, Iterable):
            if max(counts_used) >= len_counts_half:
                raise ValueError(
                    "counts_used should be less than "
                    f"{len_counts_half}, but get {max(counts_used)}."
                )
            counts = [self.afterwards.counts[i] for i in counts_used] + [
                self.afterwards.counts[i + len_counts_half] for i in counts_used
            ]
        else:
            if counts_used is not None:
                raise ValueError(f"counts_used should be Iterable, but get {type(counts_used)}.")
            counts = self.afterwards.counts

        if isinstance(pbar, tqdm.tqdm):
            qs = self.quantities(
                shots=shots,
                counts=counts,
                degree=degree,
                measure=measure,
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
            **qs,  # type: ignore
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
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        workers_num: Optional[int] = None,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> dict[str, float]:
        """Calculate entangled entropy with more information combined.

        Args:
            shots (int): Shots of the experiment on quantum machine.
            counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            measure (tuple[int, int], optional):
                Measuring range on quantum circuits. Defaults to None.
            workers_num (Optional[int], optional):
                Number of multi-processing workers,
                if sets to 1, then disable to using multi-processing;
                if not specified, then use the number of all cpu counts - 2 by `cpu_count() - 2`.
                Defaults to None.
            pbar (Optional[tqdm.tqdm], optional): Progress bar. Defaults to None.
            use_cython (bool, optional): Use cython to calculate purity cell. Defaults to True.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy, a list of each overlap, puritySD,
                purity of all system, entropy of all system,
                a list of each overlap in all system, puritySD of all system,
                degree, actual measure range, actual measure range in all system, bitstring range.
        """
        if shots is None or counts is None:
            raise ValueError("shots and counts should be specified.")

        return randomized_overlap_echo(
            shots=shots,
            counts=counts,
            degree=degree,
            measure=measure,
            backend=backend,
            workers_num=workers_num,
            pbar=pbar,
        )
