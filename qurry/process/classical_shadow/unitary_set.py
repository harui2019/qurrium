r"""
================================================================
Postprocessing - Classical Shadow - Unitary Set
(:mod:`qurry.process.classical_shadow.unitary_set`)
================================================================

The followings are unitary operators for our classical shadow implementation.

.. math::
    U_M \in \{R_X(\frac{\pi}{2}), R_Y(-\frac{\pi}{2}), R_Z(0) = \mathbb{I} \}

And the set of unitary operators :math:`U_M` will represent by following dictionary.:

0. :math:`R_X(\frac{\pi}{2})` 
1. :math:`R_Y(-\frac{\pi}{2})`
2. :math:`R_Z(0) = \mathbb{I}`

"""

from typing import Literal, Union
import numpy as np

# import numpy.typing as npt

from qiskit.circuit.gate import Gate
from qiskit.circuit.library import RXGate, RYGate, RZGate

U_M_GATES: dict[Union[Literal[0, 1, 2], int], Gate] = {
    0: RXGate(np.pi / 2),
    1: RYGate(-np.pi / 2),
    2: RZGate(0),
}
r"""The :class:`qiskit.circuit.library.Gate` objects 
for the unitary operators :math:`U_M` in the classical shadow.

The set of unitary operators :math:`U_M` will represent by following dictionary.:

{
    0: :math:`R_X(\frac{\pi}{2})`,
    1: :math:`R_Y(-\frac{\pi}{2})`,
    2: :math:`R_Z(0) = \mathbb{I}`
}
"""

# U_M_MATRIX: dict[int, npt.NDArray[np.complex128]] = {
U_M_MATRIX: dict[
    Union[Literal[0, 1, 2], int], np.ndarray[tuple[Literal[2], Literal[2]], np.dtype[np.complex128]]
] = {
    0: np.array(
        [
            [np.cos(np.pi / 4), -1j * np.sin(np.pi / 4)],
            [-1j * np.sin(np.pi / 4), np.cos(np.pi / 4)],
        ],
        dtype=np.complex128,
    ),
    1: np.array(
        [
            [np.cos(-np.pi / 4), -np.sin(-np.pi / 4)],
            [np.sin(-np.pi / 4), np.cos(-np.pi / 4)],
        ],
        dtype=np.complex128,
    ),
    2: np.array(
        [
            [np.exp(0), 0],
            [0, np.cos(0)],
        ],
        dtype=np.complex128,
    ),
}
r"""The :class:`numpy.matrix` objects 
for the unitary operators :math:`U_M` in the classical shadow.

The set of unitary operators :math:`U_M` will represent by following dictionary.:

{
    0: :math:`R_X(\frac{\pi}{2})`,
    1: :math:`R_Y(-\frac{\pi}{2})`,
    2: :math:`R_Z(0) = \mathbb{I}`
}
"""


OUTER_PRODUCT: dict[
    Union[Literal["0", "1"], str], np.ndarray[tuple[Literal[2], Literal[2]], np.dtype[np.int32]]
] = {
    "0": np.array(
        [
            [1, 0],
            [0, 0],
        ],
        dtype=np.int32,
    ),
    "1": np.array(
        [
            [0, 0],
            [0, 1],
        ],
        dtype=np.int32,
    ),
}
r"""The :class:`numpy.ndarray` objects 
for the outer product of :math:`|0\rangle` and :math:`|1\rangle`.

.. math::
    |0\rangle\langle0| = \begin{pmatrix} 1 & 0 \\ 0 & 0 \end{pmatrix}
    |1\rangle\langle1| = \begin{pmatrix} 0 & 0 \\ 0 & 1 \end{pmatrix}

The set of outer product will represent by following dictionary.:

{
    "0": :math:`|0\rangle\langle0|`,
    "1": :math:`|1\rangle\langle1|`
}
"""

IDENTITY = np.array(
    [
        [1, 0],
        [0, 1],
    ],
    dtype=np.int32,
)
r"""The :class:`numpy.ndarray` objects
for the identity matrix.

It's just :math:`\mathbb{I} = \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}`.

What a simple matrix!
"""
