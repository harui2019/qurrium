"""
=========================================================================================
Postprocessing - Randomized Measure - Entangled Entropy - Container
(:mod:`qurry.process.randomized_measure.entangled_entropy.container`)
=========================================================================================

"""

from typing import Union, Optional, Literal, TypedDict, NamedTuple
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


GenericFloatType = Union[np.float64, float]
"""The generic float type by numpy or python."""


class EntangledEntropyResult(TypedDict, total=False):
    """The return type of the post-processing for entangled entropy."""

    purity: GenericFloatType
    """The purity of the system."""
    entropy: GenericFloatType
    """The entropy of the system."""
    puritySD: GenericFloatType
    """The standard deviation of the purity."""
    entropySD: GenericFloatType
    """The standard deviation of the entropy."""
    purityCells: Union[dict[int, np.float64], dict[int, float]]
    """The purity of each single count."""
    # new added
    num_classical_registers: int
    """The number of classical registers."""
    classical_registers: Optional[list[int]]
    """The list of the index of the selected classical registers."""
    classical_registers_actually: list[int]
    """The list of the index of the selected classical registers which is actually used."""
    # refactored
    counts_num: int
    """The number of counts."""
    taking_time: GenericFloatType
    """The calculation time."""


class EntangledEntropyResultMitigated(EntangledEntropyResult):
    """The return type of the post-processing for entangled entropy with error mitigation."""

    # refactored
    all_system_source: Union[str, Literal["independent", "null_counts"]]
    """The name of source of all system.

    - independent: The all system is calculated independently.
    - null_counts: No counts exist.
    """

    purityAllSys: GenericFloatType
    """The purity of the all system."""
    entropyAllSys: GenericFloatType
    """The entropy of the all system."""
    puritySDAllSys: GenericFloatType
    """The standard deviation of the purity of the all system."""
    entropySDAllSys: GenericFloatType
    """The standard deviation of the entropy of the all system."""
    purityCellsAllSys: Union[dict[int, np.float64], dict[int, float]]
    """The purity of each single count."""

    # new added
    num_classical_registers_all_sys: int
    """The number of classical registers of all system."""
    classical_registers_all_sys: Optional[list[int]]
    """The list of the index of the selected classical registers."""
    classical_registers_actually_all_sys: list[int]
    """The list of the index of the selected classical registers which is actually used."""

    # mitigated info
    errorRate: GenericFloatType
    """The error rate of the measurement from depolarizing error migigation calculated."""
    mitigatedPurity: GenericFloatType
    """The mitigated purity."""
    mitigatedEntropy: GenericFloatType
    """The mitigated entropy."""

    # refactored
    taking_time_all_sys: GenericFloatType
    """The calculation time of the all system."""


class ExistedAllSystemInfo(NamedTuple):
    """Existed all system information"""

    source: str
    """The source of all system."""

    purityAllSys: GenericFloatType
    """The purity of the all system."""
    entropyAllSys: GenericFloatType
    """The entropy of the all system."""
    puritySDAllSys: GenericFloatType
    """The standard deviation of the purity of the all system."""
    entropySDAllSys: GenericFloatType
    """The standard deviation of the entropy of the all system."""
    purityCellsAllSys: Union[dict[int, np.float64], dict[int, float]]
    """The purity of each single count."""

    # new added
    num_classical_registers_all_sys: int
    """The number of classical registers of all system."""
    classical_registers_all_sys: Optional[list[int]]
    """The list of the index of the selected classical registers."""
    classical_registers_actually_all_sys: list[int]
    """The list of the index of the selected classical registers which is actually used."""

    # refactored
    taking_time_all_sys: GenericFloatType
    """The calculation time of the all system."""


class ExistedAllSystemInfoInput(TypedDict, total=False):
    """Existed all system information"""

    source: str
    """The source of all system."""

    purityAllSys: GenericFloatType
    """The purity of the all system."""
    entropyAllSys: GenericFloatType
    """The entropy of the all system."""
    puritySDAllSys: GenericFloatType
    """The standard deviation of the purity of the all system."""
    entropySDAllSys: GenericFloatType
    """The standard deviation of the entropy of the all system."""
    purityCellsAllSys: Union[dict[int, np.float64], dict[int, float]]
    """The purity of each single count."""

    # new added
    num_classical_registers_all_sys: int
    """The number of classical registers of all system."""
    classical_registers_all_sys: Optional[list[int]]
    """The list of the index of the selected classical registers."""
    classical_registers_actually_all_sys: list[int]
    """The list of the index of the selected classical registers which is actually used."""

    # refactored
    taking_time_all_sys: GenericFloatType
    """The calculation time of the all system."""
