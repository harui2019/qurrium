from typing import Union, Optional, NamedTuple, TypeVar, Generic
from qiskit.result import Result

from ..tool import Configuration

T = TypeVar('T')

Counts = Union[dict[str, int], list[dict[str, int]]]
Quantity = dict[float]

# TagsKey
TagKeyAllowable = Union[str, int, float, bool]
TagKeysAllowable = Union[tuple[TagKeyAllowable], TagKeyAllowable]

# TagsValue
TagMapBaseType = dict[list[T]]

TagMapExpsIDType = TagMapBaseType[str]
TagMapIndexType = TagMapBaseType[Union[str, int]]
TagMapQuantityType = TagMapBaseType[dict[float]]
TagMapCountsType = TagMapBaseType[dict[Counts]]
TagMapResultType = TagMapBaseType[Result]

TagMap = Configuration(
    name='TagMap',
    default={
        'all': [], 'noTags': [],
    },
)

