"""Post Processing - Utils - Randomized (:mod:`qurry.process.utils.randomized`)"""

import numpy as np
from ..availability import availability

# pylint: disable=import-error,no-name-in-module
from ...boorust.randomized import hamming_distance_rust, ensemble_cell_rust  # type: ignore


BACKEND_AVAILABLE = availability(
    "utils.randomized", [("Rust", True, None), ("Cython", "Depr.", None)]
)


def hamming_distance(str1: str, str2: str) -> int:
    """Calculate the Hamming distance between two bit strings.

    Args:
        str1 (str): First string.
        str2 (str): Second string.

    Returns:
        int: Distance between strings.

    Raises:
        ValueError: Strings not same length.
    """
    if len(str1) != len(str2):
        raise ValueError("Strings not same length.")
    return sum(s1 != s2 for s1, s2 in zip(str1, str2))


def ensemble_cell(
    s_i: str, s_i_meas: int, s_j: str, s_j_meas: int, a_num: int, shots: int
) -> np.float64:
    """Calculate the value of two counts from qubits in ensemble average.

    Args:
        s_i (str): First count's qubits arrange.
        s_i_meas (int): First count.
        s_j (str): Second count's qubits arrange.
        s_j_meas (int): Second count.
        a_num (int): Degree of freedom.
        shots (int): Shots of executation.

    Returns:
        float: the value of two counts from qubits in ensemble average.
    """
    diff = sum(s1 != s2 for s1, s2 in zip(s_i, s_j))
    return (2**a_num) * ((-2) ** (-diff)) * (s_i_meas / shots) * (s_j_meas / shots)


__all__ = ["hamming_distance", "ensemble_cell", "hamming_distance_rust", "ensemble_cell_rust"]
