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
    
    TagMap,
)
from .exceptions import *
from .randomized import (
    RXmatrix, RYmatrix, RZmatrix,
    makeTwoBitStr, makeTwoBitStrOneLiner, haarBase
)
# Mori
try:
    from .mori.attrdict import argdict
    from .mori.jsonablize import Parse as jsonablize, quickJSONExport, keyTupleLoads
    from .mori.configuration import Configuration
    from .mori.gitsync import syncControl
except:
    from .backup.attrdict import argdict
    from .backup.jsonablize import Parse as jsonablize, quickJSONExport, keyTupleLoads
    from .backup.configuration import Configuration
    from .backup.gitsync import syncControl

import numpy as np

pauliMatrix = {
    'rx': RXmatrix,
    'ry': RYmatrix,
    'rz': RZmatrix
}


