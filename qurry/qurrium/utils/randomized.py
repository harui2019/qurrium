"""
================================================================
Randomized Measure Kit for Qurry 
(:mod:`qurry.qurrium.utils.randomized`)
================================================================

"""

from typing import Union, Optional
import numpy as np
from qiskit.quantum_info import random_unitary, Operator

RXmatrix = np.array([[0, 1], [1, 0]])
"""Pauli-X matrix"""
RYmatrix = np.array([[0, -1j], [1j, 0]])
"""Pauli-Y matrix"""
RZmatrix = np.array([[1, 0], [0, -1]])
"""Pauli-Z matrix"""


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


def qubit_operator_to_pauli_coeff(
    rho: np.ndarray,
) -> list[tuple[Union[float, np.float64], Union[float, np.float64]]]:
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
    unitary_loc: tuple[int, int], seed: Optional[int] = None
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
) -> dict[int, list[tuple[Union[float, np.float64], Union[float, np.float64]]]]:
    """Transform a list of unitary operators in :cls:`numpy.ndarray`
    a list of pauli coefficients.

    Args:
        unitary_loc (tuple[int, int]): The location of unitary operator.
        unitary_op_list (list[np.ndarray]): The list of unitary operators.

    Returns:
        dict[int, list[tuple[float, float]]]: The list of pauli coefficients.
    """
    return {i: qubit_operator_to_pauli_coeff(unitary_op_list[i]) for i in range(*unitary_loc)}
