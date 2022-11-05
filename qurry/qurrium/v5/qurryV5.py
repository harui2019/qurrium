from qiskit import (
    execute, transpile,
    QuantumRegister, QuantumCircuit
)
from qiskit_aer import AerProvider
from qiskit.quantum_info import Operator
from qiskit.circuit import Gate, Instruction
from qiskit.result import Result
from qiskit.providers import Backend, JobError, JobStatus
from qiskit.providers.ibmq import IBMQBackend, IBMQJobManager, AccountProvider
from qiskit.providers.ibmq.managed import (
    ManagedJobSet,
    # ManagedJob,
    ManagedResults,
    IBMQManagedResultDataNotAvailable,
    # IBMQJobManagerInvalidStateError,
    # IBMQJobManagerUnknownJobSet
)

import glob
import json
import gc
import warnings
import datetime
import time
import os
from uuid import uuid4
from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, overload
from abc import abstractmethod, abstractclassmethod
from collections import namedtuple
from matplotlib.figure import Figure

from ...mori import (
    defaultConfig,
    attributedDict,
    defaultConfig,
    syncControl,
    jsonablize,
    quickJSONExport,
    sortHashableAhead,
    TagMap,
)
from ...mori.type import TagMapType
from ...util import Gajima, ResoureWatch

from ..declare.default import (
    transpileConfig,
    managerRunConfig,
    runConfig,
    ResoureWatchConfig,
    containChecker,
)
from .container import argsCore, argsMain, expsCore, expsMain
from ..construct import decomposer
from ...exceptions import (
    UnconfiguredWarning,
    InvalidConfiguratedWarning,
)
from ..declare.type import Quantity, Counts, waveGetter, waveReturn

# Qurry V0.5.0 - a Qiskit Macro


class QurryV5:
    """Qurry V0.5.0
    The qiskit Macro.
    ~Create countless adventure, legacy and tales.~
    """
    __version__ = (0, 5, 0)

    
    