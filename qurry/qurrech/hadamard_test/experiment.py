"""
================================================================
Wave Function Overlap - Hadamard Test Experiment
(:mod:`qurry.qurrech.hadamard_test.experiment`)
================================================================

"""

from typing import Optional, Hashable, NamedTuple

from .analysis import EchoHadamardAnalysis
from ...qurrium.experiment import ExperimentPrototype
from ...process.hadamard_test import hadamard_overlap_echo as overlap_echo


class EchoHadamardArguments(NamedTuple):
    """Arguments for the experiment."""

    exp_name: str = "exps"
    wave_key_2: Hashable = None
    degree: Optional[tuple[int, int]] = None


class EchoHadamardExperiment(ExperimentPrototype):
    """The experiment for calculating entangled entropy with more information combined."""

    __name__ = "qurrechHadamard.Experiment"
    shortName = "qurrech_hadamard.exp"

    Arguments = EchoHadamardArguments
    args: EchoHadamardArguments

    analysis_container = EchoHadamardAnalysis
    """The container class responding to this QurryV5 class."""

    def analyze(self) -> EchoHadamardAnalysis:
        """Calculate entangled entropy with more information combined.

        Args:
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            workers_num (Optional[int], optional):
                Number of multi-processing workers,
                if sets to 1, then disable to using multi-processing;
                if not specified, the use 3/4 of cpu counts by `round(cpu_count*3/4)`.
                Defaults to None.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy.
        """

        shots = self.commons.shots
        counts = self.afterwards.counts

        qs = self.quantities(
            shots=shots,
            counts=counts,
        )

        serial = len(self.reports)
        analysis = self.analysis_container(
            serial=serial,
            shots=shots,
            **qs,  # type: ignore
        )

        self.reports[serial] = analysis
        return analysis

    @classmethod
    def quantities(
        cls,
        shots: Optional[int] = None,
        counts: Optional[list[dict[str, int]]] = None,
    ) -> dict[str, float]:
        """Calculate entangled entropy with more information combined.

        Args:
            shots (int): Shots of the experiment on quantum machine.
            counts (list[dict[str, int]]): Counts of the experiment on quantum machine.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy.
        """

        if shots is None or counts is None:
            raise ValueError("shots and counts should be specified.")

        return overlap_echo(
            shots=shots,
            counts=counts,
        )
