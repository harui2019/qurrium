"""
================================================================
Second Renyi Entropy - Hadamard Test Experiment
(:mod:`qurry.qurrent.hadamard_test.experiment`)
================================================================

"""

from typing import Optional, NamedTuple

from .analysis import EntropyHadamardAnalysis
from ...qurrium.experiment import ExperimentPrototype
from ...process.hadamard_test import hadamard_entangled_entropy


class EntropyHadamardArguments(NamedTuple):
    """Arguments for the experiment."""

    exp_name: str = "exps"
    degree: Optional[tuple[int, int]] = None


class EntropyHadamardExperiment(ExperimentPrototype):
    """Hadamard test for entanglement entropy."""

    __name__ = "qurrentHadamard.Experiment"
    shortName = "qurrent_hadamard.exp"

    Arguments = EntropyHadamardArguments
    args: EntropyHadamardArguments

    analysis_container = EntropyHadamardAnalysis
    """The container class responding to this QurryV5 class."""

    def analyze(self) -> EntropyHadamardAnalysis:
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

        return hadamard_entangled_entropy(
            shots=shots,
            counts=counts,
        )
