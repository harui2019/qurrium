"""
===========================================================
EntropyMeasureRandomizedV1 - Analysis
(:mod:`qurry.qurrent.randomized_measure_v1.analysis`)
===========================================================

This is a deprecated version of the randomized measure module.

"""

from typing import Union, Optional, NamedTuple, Iterable, Literal

from ...qurrium.analysis import AnalysisPrototype


class EntropyMeasureRandomizedV1Analysis(AnalysisPrototype):
    """The container for the analysis of :cls:`EntropyRandomizedExperiment`."""

    __name__ = "qurrentRandomized.Analysis"
    shortName = "qurrent_haar.report"

    class AnalysisInput(NamedTuple):
        """To set the analysis."""

        degree: tuple[int, int]
        """The range of partition."""
        shots: int
        """The number of shots."""
        unitary_loc: Optional[tuple[int, int]] = None
        """The location of the random unitary operator."""

    input: AnalysisInput

    class AnalysisContent(NamedTuple):
        """The content of the analysis."""

        purity: Optional[float] = None
        """The purity of the subsystem."""
        entropy: Optional[float] = None
        """The entanglement entropy of the subsystem."""
        puritySD: Optional[float] = None
        """The standard deviation of the purity of the subsystem."""
        entropySD: Optional[float] = None
        """The standard deviation of the entanglement entropy of the subsystem."""
        purityCells: Optional[dict[int, float]] = None
        """The purity of each cell of the subsystem."""
        bitStringRange: Optional[tuple[int, int]] = None
        """The qubit range of the subsystem."""

        allSystemSource: Optional[Union[str, Literal["independent"]]] = None
        """The source of the all system."""
        purityAllSys: Optional[float] = None
        """The purity of the system."""
        entropyAllSys: Optional[float] = None
        """The entanglement entropy of the system."""
        puritySDAllSys: Optional[float] = None
        """The standard deviation of the purity of the system."""
        entropySDAllSys: Optional[float] = None
        """The standard deviation of the entanglement entropy of the system."""
        purityCellsAllSys: Optional[dict[int, float]] = None
        """The purity of each cell of the system."""
        bitsStringRangeAllSys: Optional[tuple[int, int]] = None
        """The qubit range of the all system."""

        errorRate: Optional[float] = None
        """The error rate of the measurement from depolarizing error migigation calculated."""
        mitigatedPurity: Optional[float] = None
        """The mitigated purity of the subsystem."""
        mitigatedEntropy: Optional[float] = None
        """The mitigated entanglement entropy of the subsystem."""

        num_qubits: Optional[int] = None
        """The number of qubits of the system."""
        measure: Optional[tuple[str, Union[list[int], tuple[int, int]]]] = None
        """The qubit range of the measurement and text description.

        - The first element is the text description.
        - The second element is the qubit range of the measurement.

        ---
        - When the measurement is specified, it will be:

        >>> ("measure range:", (0, 3))

        - When the measurement is not specified, it will be:

        >>> ("not specified, use all qubits", (0, 3))

        - When null counts exist, it will be:

        >>> ("The following is the index of null counts.", [0, 1, 2, 3])

        """
        measureActually: Optional[tuple[int, int]] = None
        """The qubit range of the measurement actually used."""
        measureActuallyAllSys: Optional[tuple[int, int]] = None
        """The qubit range of the measurement actually used in the all system."""

        countsNum: Optional[int] = None
        """The number of counts of the experiment."""
        takingTime: Optional[float] = None
        """The taking time of the selected system."""
        takingTimeAllSys: Optional[float] = None
        """The taking time of the all system if it is calculated, 
        it will be 0 when use the all system from other analysis."""
        counts_used: Optional[Iterable[int]] = None
        """The index of the counts used.
        If not specified, then use all counts."""

        def __repr__(self):
            return f"AnalysisContent(purity={self.purity}, entropy={self.entropy}, and others)"

    @property
    def side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return [
            "purityCells",
            "purityCellsAllSys",
        ]

    content: AnalysisContent
