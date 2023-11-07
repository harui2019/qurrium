"""
================================================================
Type declarations for Qurry (:mod:`qurry.declare.type`)
================================================================

"""
from typing import Union, Sequence, TypeVar

from qiskit import QuantumRegister
from qiskit.circuit.quantumcircuit import Qubit


# TagsValue
T = TypeVar("T")
KT = TypeVar("KT")
VT = TypeVar("VT")

QubitSpecifier = Union[
    Qubit,
    QuantumRegister,
    int,
    slice,
    Sequence[Union[Qubit, int]],
]
