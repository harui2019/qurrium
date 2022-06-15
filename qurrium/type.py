from typing import Union, Optional, NamedTuple, TypeVar, Generic
from qiskit.result import Result
import warnings

from ..tool import Configuration
try:
    from .mori import (
        Configuration,
        argdict,
        syncControl,
        jsonablize,
        quickJSONExport,
        keyTupleLoads,
        TagMap,
    )
except ImportError:
    warnings.warn("Please run 'git submodule update --init --recursive' for full functional.")
    from .backup import (
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
