from qiskit.visualization.counts_visualization import hamming_distance, VisualizationError
from qiskit.quantum_info import random_unitary
# from qiskit.result import Result

import numpy as np
from typing import Callable, Iterable

# Haar Randomized Parts V0.3.0 - Qurrium

RXmatrix = np.array([[0, 1], [1, 0]])
RYmatrix = np.array([[0, -1j], [1j, 0]])
RZmatrix = np.array([[1, 0], [0, -1]])


def makeTwoBitStr(num: int, bits: list[str] = ['']) -> list[str]:
    return ((lambda bits: [
        *['0'+item for item in bits], *['1'+item for item in bits]
    ])(makeTwoBitStr(num-1, bits)) if num > 0 else bits)


makeTwoBitStrOneLiner: Callable[[int, list[str]], list[str]] = (
    lambda num, bits=['']: ((lambda bits: [
        *['0'+item for item in bits], *['1'+item for item in bits]]
    )(makeTwoBitStrOneLiner(num-1, bits)) if num > 0 else bits))


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


def ensembleCell(
    sAi: str,
    sAiMeas: int,
    sAj: str,
    sAjMeas: int,
    aNum: int,
    shots: int,
) -> float:
    """Calculate the value of two counts from qubits in ensemble average.

        - about `diff = hamming_distance(sAi, sAj)`:

            It is `hamming_distance` from `qiskit.visualization.count_visualization`.
            Due to frequently update of Qiskit and it's a simple function,
            I decide not to use source code instead of calling from `qiskit`.

        Args:
            sAi (str): First count's qubits arrange.
            sAiMeas (int): First count.
            sAj (str): Second count's qubits arrange.
            sAjMeas (int): Second count.
            aNum (int): Degree of freedom.
            shots (int): Shots of executation.

        Returns:
            float: the value of two counts from qubits in ensemble average.

    """
    diff = sum(s1 != s2 for s1, s2 in zip(sAi, sAj)
               )  # hamming_distance(sAi, sAj)
    tmp: np.float64 = np.float_power(
        2, aNum, dtype=np.float64
    )*np.float_power(
        -2, -diff, dtype=np.float64
    )*(
        np.float64(sAiMeas)/shots
    )*(
        np.float64(sAjMeas)/shots
    )
    return tmp


def densityMatrixToBloch(
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


def qubitOpToPauliCoeff(
    rho: np.array
) -> list[tuple[float]]:
    """Convert a random unitary operator matrix to a Bloch vector.

        Args:
            rho (np.array): The random unitary operator matrix.

        Returns:
            list[tuple[float]]: The bloch vector divided as tuple of real number and image number.
    """

    ax = np.trace(np.dot(rho, RXmatrix))/2
    ay = np.trace(np.dot(rho, RYmatrix))/2
    az = np.trace(np.dot(rho, RZmatrix))/2
    return [(np.float64(a.real), np.float64(a.imag)) for a in [ax, ay, az]]


def cycling_slice(target: Iterable, start: int, end: int, step: int = 1) -> Iterable:
    length = len(target)
    if (start < -length) or (end > length):
        raise IndexError("Slice out of range")
    if length <= 0:
        newString = target
    elif start < 0 and end >= 0:
        newString = target[start:] + target[:end]
    else:
        newString = target[start:end]

    return newString[::step]