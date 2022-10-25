from qiskit import (
    execute, transpile,
    QuantumRegister, QuantumCircuit
)
from qiskit.providers.aer import AerProvider
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

from ..mori import (
    defaultConfig,
    attributedDict,
    defaultConfig,
    syncControl,
    jsonablize,
    quickJSONExport,
    sortHashableAhead,
    TagMap,
)
from ..mori.type import TagMapType
from ..util import Gajima, ResoureWatch

from .declare.default import (
    transpileConfig,
    managerRunConfig,
    runConfig,
    ResoureWatchConfig,
    containChecker,
)
from .declare.container import argsCore, argsMain, expsCore, expsMain
from .construct import decomposer
from ..exceptions import (
    UnconfiguredWarning,
    InvalidConfiguratedWarning,
)
from .declare.type import Quantity, Counts, waveGetter, waveReturn

# Qurry V0.5.0 - a Qiskit Macro


def defaultCircuit(numQubit: int) -> QuantumCircuit:\
    return QuantumCircuit(
        numQubit, numQubit, name=f'qurry_default_{numQubit}')


class QurryV5:
    """Qurry V0.5.0
    The qiskit job tool
    """
    __version__ = (0, 5, 0)

    _expsBaseExceptKeys = ['sideProduct', 'result']
    _v3ArgsMapping = {
        'runConfig': 'runArgs',
    }

    class argsMultiMain(NamedTuple):
        # defaultConfig of `IBMQJobManager().run`
        # Multiple jobs shared
        shots: int = None
        backend: Backend = None
        provider: AccountProvider = None

        # IBMQJobManager() dedicated
        managerRunArgs: dict[str, any] = None

        # Other arguments of experiment
        # Multiple jobs shared
        expsName: str = None
        saveLocation: Union[Path, str] = None
        exportLocation: Path = None

        pendingStrategy: Literal['power', 'tags', 'each'] = None
        jobsType: Literal["multiJobs", "powerJobs"] = None
        isRetrieve: bool = None
        isRead: bool = None
        clear: bool = None
        independentExports: list[str] = None
        filetype: TagMap._availableFileType = None

    class expsMultiMain(NamedTuple):
        # configList
        configList: list = []
        configDict: dict = {}

        powerJobID: Union[str, list[str]] = []
        gitignore: syncControl = syncControl()

        circuitsNum: dict[str, int] = {}
        state: Literal["init", "pending", "completed"] = 'init'

    class _tagMapStateDepending(NamedTuple):
        tagMapQuantity: TagMapType[Quantity]
        tagMapCounts: TagMapType[Counts]

    class _tagMapUnexported(NamedTuple):
        tagMapResult: TagMapType[Result]

    class _tagMapNeccessary(NamedTuple):
        # with Job.json file
        tagMapExpsID: TagMapType[str]
        tagMapFiles: TagMapType[str]
        tagMapIndex: TagMapType[Union[str, int]]
        # circuitsMap
        circuitsMap: TagMapType[str]
        pendingPools: TagMapType[str]

    _generalJobKeyRequired = ['state']
    _powerJobKeyRequired = ['powerJobID'] + _generalJobKeyRequired
    _multiJobKeyRequired = [] + _generalJobKeyRequired
    _independentExportDefault = ['configDict']
    _unexport = ['configList']+[i for i in _tagMapUnexported._fields]

    _v3MultiArgsMapping = {
        'circuitsMap': 'circuitsMap',
    }
    
    