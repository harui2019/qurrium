"""
===========================================================
EchoListenRandomized - Analysis
(:mod:`qurry.qurrech.randomized_measure.analysis`)
===========================================================

"""

from typing import Optional, NamedTuple, Iterable

from ...qurrium.analysis import AnalysisPrototype


class EchoListenRandomizedAnalysis(AnalysisPrototype):
    """The analysis of loschmidt echo."""

    __name__ = "qurrechRandomized.Analysis"
    shortName = "qurrech_haar.report"

    class AnalysisInput(NamedTuple):
        """To set the analysis."""

        degree: tuple[int, int]
        """The range of partition."""
        shots: int
        """The number of shots."""
        unitary_loc: Optional[tuple[int, int]] = None
        """The location of the random unitary operator."""

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
        counts_used: Optional[Iterable[int]] = None
        """The index of the counts used.
        If not specified, then use all counts."""

        def __repr__(self):
            return f"AnalysisContent(echo={self.echo}, and others)"

    @property
    def side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return [
            "echoCells",
        ]
