"""Mori - JSON Serializer (:mod:`qurry.capsule.mori`)

## Why names Mori?

    There are many dedicated data structures for Qurrium
    If we say one of them like a tree in forest,
    then all data structures combine,
    it makes a forest or '森' read as mori in Japanese.
    Definitely NOT because I'm a DeadBeat,
    the fan of Hololive VTuber Mori Calliope,
    and I didn't want to name something after her for a not short time.

"""

from .abc import (
    DataExportable,
    DataIngestible,
    DataExportableIngestible,
    FileWritableObj,
    FileReadableObj,
    FileReadableWritableObj,
    WrittenContentType,
)
from .writers import WritableQueueUnit, WrittenQueueUnit, check_writable, UniversalWriterABC
from .tuple_key import key_tuple_loads, tuple_str_parse, tuple_str_parse_ensured

# pylint: disable=reimported
from .jsonablize import (
    parse as jsonablize,
    quick_json_write as quickJSON,
    quick_json_write,
)
# pylint: enable=reimported

__all__ = ["key_tuple_loads", "tuple_str_parse", "jsonablize", "quickJSON", "quick_json_write"]
