from .qurmagsq import MagnetSquare
from .qurrech import EchoListen
from .qurrent import EntropyMeasure
from .qurstrop import StringOperator
from .qurrium import QurryV3, QurryV4 as Qurry

from .tools import (
    backendWrapper, 
    ResoureWatch,
    version_check,
    cmdWrapper,
    pytorchCUDACheck,
)

from .version import __version__, __version_str__