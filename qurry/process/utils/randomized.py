"""
================================================================
Randomized Measure Kit for Qurry 
(:mod:`qurry.qurrium.utils.randomized`)
================================================================

"""
import warnings
from typing import Callable, Iterable, Union, Optional, Literal
import numpy as np

from ...exceptions import (
    QurryCythonImportError,
    QurryCythonUnavailableWarning,
    QurryRustImportError,
    QurryRustUnavailableWarning,
)

try:
    # from ...boorust.randomized import (  # type: ignore
    #     ensemble_cell_rust as ensemble_cell_rust_source,  # type: ignore
    #     hamming_distance_rust as hamming_distance_rust_source,  # type: ignore
    # )
    # from qurry.boorust.construct import (
    #     cycling_slice_rust as cycling_slice_rust_source,  # type: ignore
    # )
    from ...boorust import construct, randomized  # type: ignore

    ensemble_cell_rust_source = randomized.ensemble_cell_rust  # type: ignore
    hamming_distance_rust_source = randomized.hamming_distance_rust  # type: ignore
    cycling_slice_rust_source = construct.cycling_slice_rust  # type: ignore

    RUST_AVAILABLE = True
    FAILED_RUST_IMPORT = None
except ImportError as err:
    RUST_AVAILABLE = False
    FAILED_RUST_IMPORT = err

    def ensemble_cell_rust_source(*args, **kwargs):
        """Dummy function for ensemble_cell_rust."""
        raise QurryRustImportError(
            "Rust is not available, using python to calculate ensemble cell."
        ) from FAILED_RUST_IMPORT

    def hamming_distance_rust_source(*args, **kwargs):
        """Dummy function for hamming_distance_rust."""
        raise QurryRustImportError(
            "Rust is not available, using python to calculate hamming distance."
        ) from FAILED_RUST_IMPORT

    def cycling_slice_rust_source(*args, **kwargs):
        """Dummy function for cycling_slice_rust."""
        raise QurryRustImportError(
            "Rust is not available, using python to calculate cycling slice."
        ) from FAILED_RUST_IMPORT


try:
    from ...boost.randomized import (
        ensembleCell,
        cycling_slice as cycling_slice_cy_source,
    )

    CYTHON_AVAILABLE = True
    FAILED_PYX_IMPORT = None
except ImportError as err:
    FAILED_PYX_IMPORT = err
    CYTHON_AVAILABLE = False
    # pylint: disable=invalid-name, unused-argument

    def ensembleCell(*args, **kwargs):
        """Dummy function for ensembleCell."""
        raise QurryCythonImportError(
            "Cython is not available, using python to calculate ensemble cell."
        ) from FAILED_PYX_IMPORT

    def cycling_slice_cy_source(*args, **kwargs):
        """Dummy function for cycling_slice_cy."""
        raise QurryCythonImportError(
            "Cython is not available, using python to calculate cycling slice."
        ) from FAILED_PYX_IMPORT


ExistingProcessBackendLabel = Literal["Cython", "Rust", "Python"]
BackendAvailabilities: dict[ExistingProcessBackendLabel, Union[bool, ImportError]] = {
    "Cython": CYTHON_AVAILABLE if CYTHON_AVAILABLE else FAILED_PYX_IMPORT,
    "Rust": RUST_AVAILABLE if RUST_AVAILABLE else FAILED_RUST_IMPORT,
    "Python": True,
}


RXmatrix = np.array([[0, 1], [1, 0]])
"""Pauli-X matrix"""
RYmatrix = np.array([[0, -1j], [1j, 0]])
"""Pauli-Y matrix"""
RZmatrix = np.array([[1, 0], [0, -1]])
"""Pauli-Z matrix"""

# pylint: disable=unnecessary-direct-lambda-call


def make_two_bit_str(num: int, bits: Optional[list[str]] = None) -> list[str]:
    """Make a list of bit strings with length of `num`.

    Args:
        num (int): bit string length.
        bits (list[str], optional): The input for recurrsion. Defaults to [''].

    Returns:
        list[str]: The list of bit strings.
    """
    return (
        (lambda bits: [*["0" + item for item in bits], *["1" + item for item in bits]])(
            make_two_bit_str(num - 1, [""] if bits is None else [""])
        )
        if num > 0
        else bits
    )


makeTwoBitStrOneLiner: Callable[[int, list[str]], list[str]] = lambda num, bits=[""]: (
    (lambda bits: [*["0" + item for item in bits], *["1" + item for item in bits]])(
        makeTwoBitStrOneLiner(num - 1, bits)
    )
    if num > 0
    else bits
)
"""Make a list of bit strings with length of `num`. But it's an ONE LINE code.

    Args:
        num (int): bit string length.
        bits (list[str], optional): The input for recurrsion. Defaults to [''].

    Returns:
        list[str]: The list of bit strings.
"""
# pylint: enable=unnecessary-direct-lambda-call


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
        QurryRustUnavailableWarning,
    )
    return hamming_distance(str1, str2)


def ensemble_cell(
    s_i: str,
    s_i_meas: int,
    s_j: str,
    s_j_meas: int,
    a_num: int,
    shots: int,
) -> float:
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
    tmp: np.float64 = (
        np.float_power(2, a_num, dtype=np.float64)
        * np.float_power(-2, -diff, dtype=np.float64)
        * (np.float64(s_i_meas) / shots)
        * (np.float64(s_j_meas) / shots)
    )
    return tmp


def ensemble_cell_cy(
    s_i: str,
    s_i_meas: int,
    s_j: str,
    s_j_meas: int,
    a_num: int,
    shots: int,
) -> float:
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
    if CYTHON_AVAILABLE:
        return ensembleCell(s_i, s_i_meas, s_j, s_j_meas, a_num, shots)
    warnings.warn(
        "Cython is not available, using python to calculate ensemble cell."
        + f" Check: {FAILED_PYX_IMPORT}",
        QurryCythonUnavailableWarning,
    )
    return ensemble_cell(s_i, s_i_meas, s_j, s_j_meas, a_num, shots)


def ensemble_cell_rust(
    s_i: str,
    s_i_meas: int,
    s_j: str,
    s_j_meas: int,
    a_num: int,
    shots: int,
) -> float:
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
        QurryRustUnavailableWarning,
    )
    return ensemble_cell(s_i, s_i_meas, s_j, s_j_meas, a_num, shots)


def cycling_slice(target: Iterable, start: int, end: int, step: int = 1) -> Iterable:
    """Slice a iterable object with cycling.

    Args:
        target (Iterable): The target object.
        start (int): Index of start.
        end (int): Index of end.
        step (int, optional): Step of slice. Defaults to 1.

    Raises:
        IndexError: Slice out of range.

    Returns:
        Iterable: The sliced object.
    """
    length = len(target)
    slice_check = {
        "start <= -length": (start <= -length),
        "end >= length ": (end >= length),
    }
    if all(slice_check.values()):
        raise IndexError(
            "Slice out of range"
            + ", ".join([f" {k};" for k, v in slice_check.items() if not v])
        )
    if length <= 0:
        return target
    if start < 0 <= end:
        new_string = target[start:] + target[:end]
    else:
        new_string = target[start:end]

    return new_string[::step]


def cycling_slice_cy(target: Iterable, start: int, end: int, step: int = 1) -> Iterable:
    """Slice a iterable object with cycling.

    Args:
        target (Iterable): The target object.
        start (int): Index of start.
        end (int): Index of end.
        step (int, optional): Step of slice. Defaults to 1.

    Raises:
        IndexError: Slice out of range.

    Returns:
        Iterable: The sliced object.
    """
    if CYTHON_AVAILABLE:
        return cycling_slice_cy_source(target, start, end, step)
    warnings.warn(
        "Cython is not available, using python to calculate cycling slice."
        + f" Check: {FAILED_PYX_IMPORT}",
        QurryCythonUnavailableWarning,
    )
    return cycling_slice(target, start, end, step)


def cycling_slice_rust(
    target: Iterable, start: int, end: int, step: int = 1
) -> Iterable:
    """Slice a iterable object with cycling.

    Args:
        target (Iterable): The target object.
        start (int): Index of start.
        end (int): Index of end.
        step (int, optional): Step of slice. Defaults to 1.

    Raises:
        IndexError: Slice out of range.

    Returns:
        Iterable: The sliced object.
    """
    if RUST_AVAILABLE:
        return cycling_slice_rust_source(target, start, end, step)
    warnings.warn(
        "Rust is not available, using python to calculate cycling slice."
        + f" Check: {FAILED_RUST_IMPORT}",
        QurryRustUnavailableWarning,
    )
    return cycling_slice(target, start, end, step)
