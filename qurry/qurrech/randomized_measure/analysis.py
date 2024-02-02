"""
===========================================================
Wave Function Overlap - Randomized Measurement Analysis
(:mod:`qurry.qurrech.randomized_measure.analysis`)
===========================================================

"""

from typing import Optional, NamedTuple, Iterable

from ...qurrium.analysis import AnalysisPrototype


class EchoRandomizedAnalysis(AnalysisPrototype):
    """The analysis of loschmidt echo."""

    __name__ = "qurrechRandomized.Analysis"
    shortName = "qurrech_haar.report"

    class AnalysisInput(NamedTuple):
        """To set the analysis."""

        degree: tuple[int, int]
        shots: int
        unitary_loc: Optional[tuple[int, int]] = None

    class AnalysisContent(NamedTuple):
        """The content of the analysis."""

        echo: float
        """The purity of the system."""
        echoSD: float
        """The standard deviation of the purity of the system."""
        echoCells: dict[int, float]
        """The echo of each cell of the system."""
        bitStringRange: tuple[int, int]
        """The qubit range of the subsystem."""

        measureActually: Optional[tuple[int, int]] = None
        """The qubit range of the measurement actually used."""
        countsNum: Optional[int] = None
        """The number of counts of the experiment."""
        takingTime: Optional[float] = None
        """The taking time of the selected system."""

        def __repr__(self):
            return f"AnalysisContent(echo={self.echo}, and others)"

    @property
    def default_side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return [
            "echoCells",
        ]
