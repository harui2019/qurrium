"""
================================================================
EntropyMeasureHadamard - Analysis
(:mod:`qurry.qurrent.hadamard_test.analysis`)
================================================================

"""

from typing import NamedTuple, Iterable

from ...qurrium.analysis import AnalysisPrototype


class EntropyMeasureHadamardAnalysis(AnalysisPrototype):
    """The instance for the analysis of :cls:`EntropyHadamardExperiment`."""

    __name__ = "EntropyMeasureHadamardAnalysis"

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
