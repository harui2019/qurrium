"""
===========================================================
Randomized Measure Kit for Qurry 
(:mod:`qurry.qurrium.utils`)
===========================================================

"""
from typing import Callable, Iterable, Union, Optional
import numpy as np

from qiskit.quantum_info import random_unitary, Operator
from qiskit.visualization.exceptions import VisualizationError

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
    return ((lambda bits: [
        *['0'+item for item in bits], *['1'+item for item in bits]
    ])(make_two_bit_str(
        num-1, [''] if bits is None else ['']
    )) if num > 0 else bits)


makeTwoBitStrOneLiner: Callable[[int, list[str]], list[str]] = (
    lambda num, bits=['']: ((lambda bits: [
        *['0'+item for item in bits], *['1'+item for item in bits]]
    )(makeTwoBitStrOneLiner(num-1, bits)) if num > 0 else bits))
"""Make a list of bit strings with length of `num`. But it's an ONE LINE code.

    Args:
        num (int): bit string length.
        bits (list[str], optional): The input for recurrsion. Defaults to [''].

    Returns:
        list[str]: The list of bit strings.
"""
# pylint: enable=unnecessary-direct-lambda-call


def hamming_distance(str1: str, str2: str) -> int:
    """Calculate the Hamming distance between two bit strings

    From `qiskit.visualization.count_visualization`.

    Args:
        str1 (str): First string.
        str2 (str): Second string.
        Returns:    
            int: Distance between strings.
        Raises:
            VisualizationError: Strings not same length.
    """
    if len(str1) != len(str2):
        raise VisualizationError("Strings not same length.")
    return sum(s1 != s2 for s1, s2 in zip(str1, str2))


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
    diff = sum(s1 != s2 for s1, s2 in zip(s_i, s_j)
               )  # hamming_distance(sAi, sAj)
    tmp: np.float64 = np.float_power(
        2, a_num, dtype=np.float64
    )*np.float_power(
        -2, -diff, dtype=np.float64
    )*(
        np.float64(s_i_meas)/shots
    )*(
        np.float64(s_j_meas)/shots
    )
    return tmp


def density_matrix_to_bloch(
    rho: np.array
) -> list[float]:
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


def qubit_operator_to_pauli_coeff(
    rho: np.ndarray
) -> list[tuple[float]]:
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

    ax = np.trace(np.dot(rho, RXmatrix))/2
    ay = np.trace(np.dot(rho, RYmatrix))/2
    az = np.trace(np.dot(rho, RZmatrix))/2
    return [(np.float64(a.real), np.float64(a.imag)) for a in [ax, ay, az]]


def local_random_unitary(
    unitary_loc: tuple[int, int],
    seed: int = None
) -> dict[int, Operator]:
    """Generate a random unitary operator for single qubit.

    Args:
        unitary_loc (tuple[int, int]): The location of unitary operator.
        seed (int, optional): The seed of random generator. Defaults to None.

    Returns:
        dict[int, Operator]: The random unitary operator.
    """
    return {
        j: random_unitary(2, seed) for j in range(*unitary_loc)
    }


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
    return {
        i: np.array(unitary_op_list[i]).tolist() for i in range(*unitary_loc)
    }


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
        i: qubit_operator_to_pauli_coeff(unitary_op_list[i]) for i in range(*unitary_loc)
    }


def cycling_slice(
    target: Iterable,
    start: int,
    end: int,
    step: int = 1
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
    length = len(target)
    slice_check = {
        'start <= -length': (start <= -length),
        'end >= length ': (end >= length),
    }
    if all(slice_check.values()):
        raise IndexError(
            "Slice out of range" +
            ", ".join([f" {k};" for k, v in slice_check.items() if not v]))
    if length <= 0:
        return target
    if start < 0 <= end:
        new_string = target[start:] + target[:end]
    else:
        new_string = target[start:end]

    return new_string[::step]
