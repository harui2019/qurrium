"""
================================================================
Postprocessing - Utils - Randomized
(:mod:`qurry.process.utils.randomized`)
================================================================

"""

import warnings
from typing import Union
import numpy as np

from ..availability import availablility
from ..exceptions import PostProcessingRustImportError, PostProcessingRustUnavailableWarning

try:
    from ...boorust import randomized  # type: ignore

    ensemble_cell_rust_source = randomized.ensemble_cell_rust  # type: ignore
    hamming_distance_rust_source = randomized.hamming_distance_rust  # type: ignore

    RUST_AVAILABLE = True
    FAILED_RUST_IMPORT = None
except ImportError as err:
    RUST_AVAILABLE = False
    FAILED_RUST_IMPORT = err

    def ensemble_cell_rust_source(*args, **kwargs):
        """Dummy function for ensemble_cell_rust."""
        raise PostProcessingRustImportError(
            "Rust is not available, using python to calculate ensemble cell."
        ) from FAILED_RUST_IMPORT

    def hamming_distance_rust_source(*args, **kwargs):
        """Dummy function for hamming_distance_rust."""
        raise PostProcessingRustImportError(
            "Rust is not available, using python to calculate hamming distance."
        ) from FAILED_RUST_IMPORT


BACKEND_AVAILABLE = availablility(
    "utils.randomized",
    [
        ("Rust", RUST_AVAILABLE, FAILED_RUST_IMPORT),
        ("Cython", "Depr.", None),
    ],
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


def hamming_distance_rust(str1: str, str2: str) -> int:
    """Calculate the Hamming distance between two bit strings.

    Args:
        str1 (str): First string.
        str2 (str): Second string.
    Returns:
        int: Distance between strings.
    Raises:
        VisualizationError: Strings not same length.

    """
    if RUST_AVAILABLE:
        return hamming_distance_rust_source(str1, str2)
    warnings.warn(
        "Rust is not available, using python to calculate ensemble cell."
        + f" Check: {FAILED_RUST_IMPORT}",
        PostProcessingRustUnavailableWarning,
    )
    return hamming_distance(str1, str2)


def ensemble_cell(
    s_i: str,
    s_i_meas: int,
    s_j: str,
    s_j_meas: int,
    a_num: int,
    shots: int,
) -> np.float64:
    """Calculate the value of two counts from qubits in ensemble average.

    - about `diff = hamming_distance(sAi, sAj)`:

        It is `hamming_distance` from `qiskit.visualization.count_visualization`.
        Due to frequently update of Qiskit and it's a simple function,
        I decide not to use source code instead of calling from `qiskit`.

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
    diff = sum(s1 != s2 for s1, s2 in zip(s_i, s_j))  # hamming_distance(sAi, sAj)
    tmp = (
        np.float_power(2, a_num, dtype=np.float64)
        * np.float_power(-2, -diff, dtype=np.float64)
        * (np.float64(s_i_meas) / shots)
        * (np.float64(s_j_meas) / shots)
    )
    return tmp


def ensemble_cell_rust(
    s_i: str,
    s_i_meas: int,
    s_j: str,
    s_j_meas: int,
    a_num: int,
    shots: int,
) -> Union[float, np.float64]:
    """Calculate the value of two counts from qubits in ensemble average by Rust.

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
    if RUST_AVAILABLE:
        return ensemble_cell_rust_source(s_i, s_i_meas, s_j, s_j_meas, a_num, shots)
    warnings.warn(
        "Rust is not available, using python to calculate ensemble cell."
        + f" Check: {FAILED_RUST_IMPORT}",
        PostProcessingRustUnavailableWarning,
    )
    return ensemble_cell(s_i, s_i_meas, s_j, s_j_meas, a_num, shots)
