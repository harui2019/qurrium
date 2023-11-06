from .qurmagsq import MagnetSquare
from .qurrech import EchoListen
from .qurrent import EntropyMeasure
# from .qurstrop import StringOperator
from .qurrium import QurryV5 as Qurry, WavesExecuter
# from .recipe import Qurecipe

from .tools import (
    BackendWrapper,
    BackendManager,
    ResoureWatch,
    version_check,
    cmdWrapper,
    pytorchCUDACheck,
)

import qurry.boorust

from .version import __version__, __version_str__
