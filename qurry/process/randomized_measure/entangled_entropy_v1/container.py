"""
=========================================================================================
Postprocessing - Randomized Measure - Entangled Entropy V1 - Container
(:mod:`qurry.process.randomized_measure.entangled_entropy_v1.container`)
=========================================================================================

"""

from typing import Union, Optional, Literal, TypedDict
import numpy as np


class RandomizedEntangledEntropyComplex(TypedDict, total=False):
    """The result of the analysis."""

    purity: Union[np.float64, float]
    """The purity of the system."""
    entropy: Union[np.float64, float]
    """The entropy of the system."""
    puritySD: Union[np.float64, float]
    """The standard deviation of the purity."""
    entropySD: Union[np.float64, float]
    """The standard deviation of the entropy."""
    purityCells: Union[dict[int, np.float64], dict[int, float]]
    """The purity of each cell."""
    bitStringRange: Union[tuple[int, int], list[int]]
    """The range of partition on the bitstring."""

    degree: Optional[Union[list[int], tuple[int, int], int]]
    """The range of partition."""
    measureActually: tuple[int, int]
    """The range of partition refer to all qubits."""

    countsNum: int
    """The number of counts."""
    takingTime: Union[np.float64, float]
    """The time of taking during specific partition."""


class RandomizedEntangledEntropyMitigatedComplex(TypedDict, total=False):
    """The result of the analysis."""

    purity: Union[np.float64, float]
    """The purity of the system."""
    entropy: Union[np.float64, float]
    """The entropy of the system."""
    puritySD: Union[np.float64, float]
    """The standard deviation of the purity."""
    entropySD: Union[np.float64, float]
    """The standard deviation of the entropy."""
    purityCells: Union[dict[int, np.float64], dict[int, float]]
    """The purity of each cell."""
    bitStringRange: Union[tuple[int, int], list[int]]
    """The range of partition on the bitstring."""

    allSystemSource: Union[str, Literal["independent"]]
    """The source of all system."""
    purityAllSys: Union[np.float64, float]
    """The purity of all system."""
    entropyAllSys: Union[np.float64, float]
    """The entropy of all system."""
    puritySDAllSys: Union[np.float64, float]
    """The standard deviation of the purity of all system."""
    entropySDAllSys: Union[np.float64, float]
    """The standard deviation of the entropy of all system."""
    purityCellsAllSys: Union[dict[int, np.float64], dict[int, float]]
    """The purity of each cell of all system."""
    bitsStringRangeAllSys: Union[tuple[int, int], list[int]]
    """The range of partition on the bitstring of all system."""

    errorRate: Union[np.float64, float]
    """The error rate of the measurement from depolarizing error migigation calculated."""
    mitigatedPurity: Union[np.float64, float]
    """The mitigated purity."""
    mitigatedEntropy: Union[np.float64, float]
    """The mitigated entropy."""

    degree: Optional[Union[list[int], tuple[int, int], int]]
    """The range of partition."""
    num_qubits: int
    """The number of qubits of this system."""
    measure: tuple[str, Union[list[int], tuple[int, int]]]
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
    measureActually: Union[tuple[int, int], list[int]]
    """The range of partition refer to all qubits."""
    measureActuallyAllSys: Union[tuple[int, int], list[int]]
    """The range of partition refer to all qubits of all system."""

    countsNum: int
    """The number of counts."""
    takingTime: Union[np.float64, float]
    """The time of taking during specific partition."""
    takingTimeAllSys: Union[np.float64, float]
    """The taking time of the all system if it is calculated, 
    it will be 0 when use the all system from other analysis.
    """


class ExistingAllSystemSource(TypedDict):
    """Existing all system source."""

    purityCellsAllSys: dict[int, float]
    """The purity of each cell of all system."""
    bitStringRange: Union[tuple[int, int], list[int]]
    """The range of partition on the bitstring."""
    measureActually: Union[tuple[int, int], list[int]]
    """The range of partition refer to all qubits."""
    source: str
    """The source of all system."""
