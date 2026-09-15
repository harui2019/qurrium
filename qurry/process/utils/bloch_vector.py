"""Bloch Vector Utilities (:mod:`qurry.process.utils.bloch_vector`)"""

from collections.abc import Sequence
import numpy as np
import numpy.typing as npt

PAULI_X: npt.NDArray[np.complex128] = np.array([[0, 1], [1, 0]])
"""Pauli-X matrix"""
PAULI_Y: npt.NDArray[np.complex128] = np.array([[0, -1j], [1j, 0]])
"""Pauli-Y matrix"""
PAULI_Z: npt.NDArray[np.complex128] = np.array([[1, 0], [0, -1]])
"""Pauli-Z matrix"""


def density_matrix_to_bloch_vector(
    rho: npt.NDArray[np.complex128] | Sequence[Sequence[complex]],
) -> tuple[float, float, float]:
    """Convert a density matrix to a Bloch vector.

    Args:
        rho (npt.NDArray[np.complex128] | Sequence[Sequence[complex]]):
            The density matrix.
            It can be a :class:`~numpy.ndarray` or :class:`list[list[complex]]`.
            The matrix should be a 2x2 matrix.

    Returns:
        The bloch vector.
    """

    return (
        float(np.trace(np.dot(rho, PAULI_X)).real),
        float(np.trace(np.dot(rho, PAULI_Y)).real),
        float(np.trace(np.dot(rho, PAULI_Z)).real),
    )
