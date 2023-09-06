from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Operator
from qiskit.circuit.gate import Gate
from qiskit.circuit.instruction import Instruction
from qiskit.circuit.quantumcircuit import Qubit
from qiskit.result import Result

from typing import Union, Sequence, TypeVar, Optional

# TagsValue
T = TypeVar("T")
KT = TypeVar("KT")
VT = TypeVar("VT")

# waveGetter methods
waveGetter = Union[list[T], T]
waveReturn = Union[Gate, Operator, Instruction, QuantumCircuit]

QubitSpecifier = Union[
    Qubit,
    QuantumRegister,
    int,
    slice,
    Sequence[Union[Qubit, int]],
]