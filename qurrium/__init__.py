from .qurry import Qurry, defaultCircuit
from .type import (
    TagKeysAllowable,
    TagMapExpsIDType,
    TagMapIndexType,
    TagMapQuantityType,
    TagMapCountsType,
    TagMapResultType,
    Quantity,
    Counts,
)
from .exceptions import *
from .randomized import (
    RXmatrix, RYmatrix, RZmatrix,
    makeTwoBitStr, makeTwoBitStrOneLiner, haarBase
)
# Mori
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

pauliMatrix = {
    'rx': RXmatrix,
    'ry': RYmatrix,
    'rz': RZmatrix
}


