"""
=========================================================================================
Postprocessing - Randomized Measure - Entangled Entropy - Container
(:mod:`qurry.process.randomized_measure.entangled_entropy.container`)
=========================================================================================

"""

from typing import Union, Optional, Literal, TypedDict, NamedTuple
import numpy as np


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
