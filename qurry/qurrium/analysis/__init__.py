"""analysis (:mod:`qurry.qurrium.analysis`)"""

from .container import AnalysesContainer
from .analysis import AnalysisPrototype, _R
from .declare import AnalyzeArgs, _RA, SpecificAnalyzeArgs
from .ers import (
    AnalysisResultsPrototype,
    _RR,
    AnalysisMiddlewarePrototype,
    _RM,
    ProcessEntriesPrototype,
    _PE,
)
