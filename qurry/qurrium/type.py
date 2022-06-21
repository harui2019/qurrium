from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.circuit.gate import Gate
from qiskit.circuit.instruction import Instruction
from qiskit.result import Result

from typing import Union, Optional, NamedTuple, TypeVar, Generic

import warnings

from .mori import (
    Configuration,
    argdict,
    syncControl,
    jsonablize,
    quickJSONExport,
    keyTupleLoads,
    TagMap,
)

T = TypeVar('T')

Counts = Union[dict[str, int], list[dict[str, int]]]
Quantity = dict[float]

# TagsKey
TagKeyAllowable = Union[str, int, float, bool]
TagKeysAllowable = Union[tuple[TagKeyAllowable], TagKeyAllowable]

# TagsValue
TagMapBaseType = TagMap[T]

TagMapExpsIDType = TagMapBaseType[str]
TagMapIndexType = TagMapBaseType[Union[str, int]]
TagMapQuantityType = TagMapBaseType[dict[float]]
TagMapCountsType = TagMapBaseType[dict[Counts]]
TagMapResultType = TagMapBaseType[Result]

# waveGetter methods
waveGetter = Union[list[T], T]
waveReturn = Union[Gate, Operator, Instruction, QuantumCircuit]
