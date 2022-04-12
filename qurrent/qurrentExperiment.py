from qiskit import (
    Aer,
    execute,
    transpile,
    QuantumRegister,
    ClassicalRegister,
    QuantumCircuit)
from qiskit.tools import *
from qiskit.visualization import *

from qiskit.quantum_info import Operator
from qiskit.circuit.gate import Gate
from qiskit.result import Result

from qiskit.providers import Backend, BaseJob, JobError
from qiskit.providers.ibmq import IBMQBackend
from qiskit.providers.ibmq.managed import (
    IBMQJobManager,
    ManagedJobSet,
    ManagedResults,
    IBMQJobManagerInvalidStateError,
    IBMQJobManagerUnknownJobSet)
from qiskit.providers.ibmq.accountprovider import AccountProvider

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

import numpy as np
import glob
import json
import gc
import warnings

from math import pi
from uuid import uuid4
from pathlib import Path
from typing import (
    Union,
    Optional,
    Annotated,
    Callable
)

from ..tool import (
    Configuration,
    argdict,
    syncControl,
    jsonablize,
    quickJSONExport,
    keyTupleLoads)
from ..qurry import (
    Qurry, 
    defaultCircuit,
    expsConfig,
    expsBase,
    expsItem, 
    dataTagAllow,
    dataTagsAllow,
)
# EntropyMeasure V0.3.1 - Quantum Renyi Entropy - Qurrent

_expsConfig = expsConfig(
    name="qurrentConfig",
    defaultArg={
        # Variants of experiment.
        'wave': None,
        'degree': None,
    },
)

_expsBase = expsBase(
    name="qurrentExpsBase",
    expsConfig = _expsConfig,
    defaultArg = {
        # Reault of experiment.
        'purtiy': -100,
        'entropy': -100,
    },
)