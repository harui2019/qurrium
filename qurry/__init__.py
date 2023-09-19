from .qurmagsq import MagnetSquare
from .qurrech import EchoListen
from .qurrent import EntropyMeasure
# from .qurstrop import StringOperator
from .qurrium import QurryV5 as Qurry, WavesExecuter
# from .recipe import Qurecipe

from .tools import (
    backendWrapper,
    backendManager,
    ResoureWatch,
    version_check,
    cmdWrapper,
    pytorchCUDACheck,
)

from .version import __version__, __version_str__
