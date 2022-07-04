from .argrecord import argdict, argTuple
from .jsonablize import Parse as jsonablize, quickJSONExport, sortHashableAhead
from .configuration import Configuration
from .gitsync import syncControl

from .tagmaps.tagmaps import TagMap, keyTupleLoads, tupleStrParse
from .tagmaps.quantity import quantitiesMean, tagMapQuantityMean, Q
