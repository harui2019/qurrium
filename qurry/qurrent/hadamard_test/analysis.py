"""
================================================================
EntropyMeasureHadamard - Analysis
(:mod:`qurry.qurrent.hadamard_test.analysis`)
================================================================

"""

from typing import NamedTuple, Iterable

from ...qurrium.analysis import AnalysisPrototype
from ...process.hadamard_test import hadamard_entangled_entropy


class EntropyMeasureHadamardAnalysis(AnalysisPrototype):
    """The instance for the analysis of :cls:`EntropyHadamardExperiment`."""

    __name__ = "qurrentHadamard.Analysis"
    shortName = "qurrent_hadamard.report"

    class AnalysisInput(NamedTuple):
        """To set the analysis."""

    input: AnalysisInput

    class AnalysisContent(NamedTuple):
        """The content of the analysis."""

        purity: float
        """The purity of the system."""
        entropy: float
        """The entanglement entropy of the system."""

        def __repr__(self):
            return f"AnalysisContent(purity={self.purity}, entropy={self.entropy}, and others)"

    content: AnalysisContent

    @property
    def side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return []

    @classmethod
    def quantities(
        cls,
        shots: int,
        counts: list[dict[str, int]],
    ) -> dict[str, float]:
        """Calculate entangled entropy with more information combined.

        Args:
            shots (int): Shots of the experiment on quantum machine.
            counts (list[dict[str, int]]): Counts of the experiment on quantum machine.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy.
        """

        result = hadamard_entangled_entropy(
            shots=shots,
            counts=counts,
        )
        return result
