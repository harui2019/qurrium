from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.circuit.gate import Gate
from qiskit.circuit.instruction import Instruction
from qiskit.result import Result

from typing import Union, Hashable, TypeVar, Generic, MutableMapping
import warnings

Counts = Union[dict[str, int], list[dict[str, int]]]
Quantity = dict[str, float]

# TagsValue
T = TypeVar("T")
KT = TypeVar("KT")
VT = TypeVar("VT")

# waveGetter methods
waveGetter = Union[list[T], T]
waveReturn = Union[Gate, Operator, Instruction, QuantumCircuit]

# WaveContainer
waveContainerType = MutableMapping[Hashable, QuantumCircuit]