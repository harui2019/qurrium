__version__ = '0.3.4'

from .qurmagsq import MagnetSquare
from .qurrech import EchoListen
from .qurrent import EntropyMeasure
from .qurstrop import StringOperator
from .qurrium import Qurry

from .util import (
    backendWrapper, 
    ResoureWatch,
    cmdWrapper,
    pytorchCUDACheck,
)