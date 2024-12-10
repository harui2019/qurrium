"""
================================================================
Wave Function Overlap - Hadamard Test Analysis
(:mod:`qurry.qurrech.hadamard_test.analysis`)
================================================================

"""

from typing import NamedTuple, Iterable

from ...qurrium.analysis import AnalysisPrototype


class EchoListenHadamardAnalysis(AnalysisPrototype):
    """The analysis for calculating entangled entropy with more information combined."""

    __name__ = "EchoListenHadamardAnalysis"

    class AnalysisInput(NamedTuple):
        """To set the analysis."""

    input: AnalysisInput

    class AnalysisContent(NamedTuple):
        """The content of the analysis."""

        echo: float
        """The purity of the system."""

        def __repr__(self):
            return f"AnalysisContent(echo={self.echo}, and others)"

    content: AnalysisContent

    @property
    def side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return []
