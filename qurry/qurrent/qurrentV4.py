from qiskit import (
    QuantumRegister,
    ClassicalRegister,
    QuantumCircuit
)
from qiskit.result import Result
from qiskit.providers.ibmq.managed import ManagedResults

import numpy as np
import warnings
from math import pi
from typing import Union, Optional, NamedTuple

from ..qurrium import QurryV4

# EntropyMeasure V0.4.0 - Measuring Renyi Entropy - Qurrent


class EntropyMeasureV3(QurryV4):
    """EntropyMeasure V0.4.0 of qurrech
    """

    """ Configuration """

    class argsCore(NamedTuple):
        expsName: str = 'exps',
        wave: Union[QuantumCircuit, any, None] = None,
        degree: Optional[int] = None,
        

    def initialize(self) -> dict[str, any]:

        self._expsBase = self.expsBase()
        self._expsHint = self.expsHint()
        self._expsMultiBase = self.expsMultiBase()
        self.shortName = 'qurry'
        self.__name__ = 'Qurry'