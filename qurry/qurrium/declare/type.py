from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.circuit.gate import Gate
from qiskit.circuit.instruction import Instruction
from qiskit.result import Result

from typing import Union, Optional, NamedTuple, TypeVar, Generic
import warnings

Counts = Union[dict[str, int], list[dict[str, int]]]
Quantity = dict[str, float]

# TagsValue
T = TypeVar("T")

# waveGetter methods
waveGetter = Union[list[T], T]
waveReturn = Union[Gate, Operator, Instruction, QuantumCircuit]
