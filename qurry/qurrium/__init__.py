"""
================================================================
Qurrium (:mod:`qurry.qurry.qurrium`)
================================================================

"""

from .qurrium import QurryPrototype
from .experiment import ExperimentPrototype, ArgumentsPrototype
from .analysis import AnalysisPrototype
from .samplingqurry import QurryV5 as SamplingExecuter
from .wavesqurry import WavesExecuter

from .utils import decomposer
