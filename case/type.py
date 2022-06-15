from qiskit import QuantumRegister
from qiskit.circuit.quantumcircuit import Qubit
from typing import Union, Sequence

# Qubit type annotations.
QubitSpecifier = Union[
    Qubit,
    QuantumRegister,
    int,
    slice,
    Sequence[Union[Qubit, int]],
]
