"""
================================================================
Randomized Measure Kit for Qurry 
(:mod:`qurry.qurrium.utils.randomized`)
================================================================

"""
import warnings
from typing import Callable, Iterable, Union, Optional, Literal
import numpy as np
from qiskit.quantum_info import random_unitary, Operator

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
            + f" More infomation about this error: {err}",
        )

    def hamming_distance_rust_source(*args, **kwargs):
        """Dummy function for hamming_distance_rust."""
        raise QurryRustImportError(
            "Rust is not available, using python to calculate hamming distance."
            + f" More infomation about this error: {err}",
        )

    def cycling_slice_rust_source(*args, **kwargs):
        """Dummy function for cycling_slice_rust."""
        raise QurryRustImportError(
            "Rust is not available, using python to calculate cycling slice."
            + f" More infomation about this error: {err}",
        )


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
            + f" More infomation about this error: {FAILED_PYX_IMPORT}",
        )

    def cycling_slice_cy_source(*args, **kwargs):
        """Dummy function for cycling_slice_cy."""
        raise QurryCythonImportError(
            "Cython is not available, using python to calculate cycling slice."
            + f" More infomation about this error: {FAILED_PYX_IMPORT}",
        )


ExistingProcessBackendLabel = Literal["Cython", "Rust", "Python"]
BackendAvailabilities: dict[
    ExistingProcessBackendLabel, Union[bool, ImportError]
] = {
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


def density_matrix_to_bloch(rho: np.array) -> list[float]:
    """Convert a density matrix to a Bloch vector.

    Args:
        rho (np.array): The density matrix.

    Returns:
        list[np.complex128]: The bloch vector.
    """

    ax = np.trace(np.dot(rho, RXmatrix)).real
    ay = np.trace(np.dot(rho, RYmatrix)).real
    az = np.trace(np.dot(rho, RZmatrix)).real
    return [ax, ay, az]


def qubit_operator_to_pauli_coeff(rho: np.ndarray) -> list[tuple[float]]:
    """Convert a random unitary operator matrix to a Bloch vector.

    Args:
        rho (np.array): The random unitary operator matrix.

    Returns:
        list[tuple[float]]: The bloch vector divided as tuple of real number and image number.
    """
    # Please let me know the outcome of the final duel between you guys.
    # Numpy and Cython, about the issue https://github.com/cython/cython/issues/3573
    # How the fxxk to write this sxxt, numpy code in cython?
    # This function would nerver be rewritten in cython until this issue done.

    ax = np.trace(np.dot(rho, RXmatrix)) / 2
    ay = np.trace(np.dot(rho, RYmatrix)) / 2
    az = np.trace(np.dot(rho, RZmatrix)) / 2
    return [(np.float64(a.real), np.float64(a.imag)) for a in [ax, ay, az]]


def local_random_unitary(
    unitary_loc: tuple[int, int], seed: int = None
) -> dict[int, Operator]:
    """Generate a random unitary operator for single qubit.

    Args:
        unitary_loc (tuple[int, int]): The location of unitary operator.
        seed (int, optional): The seed of random generator. Defaults to None.

    Returns:
        dict[int, Operator]: The random unitary operator.
    """
    return {j: random_unitary(2, seed) for j in range(*unitary_loc)}


def local_random_unitary_operators(
    unitary_loc: tuple[int, int],
    unitary_op_list: Union[list[np.ndarray], dict[int, Operator]],
) -> dict[int, list[np.ndarray]]:
    """Transform a list of unitary operators in :cls:`qiskit.quantum_info.operator.Operator`
    a list of unitary operators in :cls:`numpy.ndarray`.

    Args:
        unitary_loc (tuple[int, int]): The location of unitary operator.
        unitary_op_list (Union[list[np.ndarray], dict[int, Operator]]):
            The list of unitary operators.

    Returns:
        dict[int, list[np.ndarray]]: The list of unitary operators.
    """
    return {i: np.array(unitary_op_list[i]).tolist() for i in range(*unitary_loc)}


def local_random_unitary_pauli_coeff(
    unitary_loc: tuple[int, int],
    unitary_op_list: list[np.ndarray],
) -> dict[int, list[tuple[float, float]]]:
    """Transform a list of unitary operators in :cls:`numpy.ndarray`
    a list of pauli coefficients.

    Args:
        unitary_loc (tuple[int, int]): The location of unitary operator.
        unitary_op_list (list[np.ndarray]): The list of unitary operators.

    Returns:
        dict[int, list[tuple[float, float]]]: The list of pauli coefficients.
    """
    return {
        i: qubit_operator_to_pauli_coeff(unitary_op_list[i])
        for i in range(*unitary_loc)
    }
