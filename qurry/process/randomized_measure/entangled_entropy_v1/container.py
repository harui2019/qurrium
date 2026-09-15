"""Post Processing - Randomized Measure - Entangled Entropy V1 - Container
(:mod:`qurry.process.randomized_measure.entangled_entropy_v1.container`)

"""

from typing import Literal, TypedDict
import numpy as np

from ...utils import FloatType


class TargetSystemResultV1(TypedDict):
    """The result of the analysis."""

    purity: FloatType
    """The purity of the system."""
    entropy: FloatType
    """The entropy of the system."""
    puritySD: FloatType
    """The standard deviation of the purity."""
    entropySD: FloatType
    """The standard deviation of the entropy."""
    purityCells: dict[int, np.float64] | dict[int, float]
    """The purity of each cell."""
    bitStringRange: tuple[int, int] | list[int]
    """The range of partition on the bitstring."""

    degree: tuple[int, int] | int | None
    """The range of partition."""
    measureActually: tuple[int, int]
    """The range of partition refer to all qubits."""

    countsNum: int
    """The number of counts."""
    num_qubits: int
    """The number of qubits of this system."""
    takingTime: FloatType
    """The time of taking during specific partition."""


class AllSystemResultV1(TargetSystemResultV1):
    """The result of the analysis."""

    allSystemSource: Literal["independent"] | str
    """The source of all system."""


def isvalid_all_system_result_v1(all_sys_result: AllSystemResultV1) -> None:
    """Verify if the given AllSystemResultV1 object is valid.

    Args:
        all_sys_result (AllSystemResultV1):
    """
    required_keys = [
        "purity",
        "entropy",
        "puritySD",
        "entropySD",
        "purityCells",
        "bitStringRange",
        "degree",
        "measureActually",
        "countsNum",
        "num_qubits",
        "takingTime",
        "allSystemSource",
    ]
    for key in required_keys:
        if key not in all_sys_result:
            raise ValueError(f"The key '{key}' is missing in AllSystemResultV1 object.")
