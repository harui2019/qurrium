from typing import Union, Optional, NamedTuple, TypeVar, Generic

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

