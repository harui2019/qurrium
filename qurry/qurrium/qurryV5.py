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
from .construct import decomposer
from ..exceptions import (
    UnconfiguredWarning,
    InvalidConfiguratedWarning,
)
from .declare.type import Quantity, Counts, waveGetter, waveReturn

# Qurry V0.5.0 - a Qiskit Macro


def defaultCircuit(numQubit: int) -> QuantumCircuit:
    return QuantumCircuit(
        numQubit, numQubit, name=f'qurry_default_{numQubit}')


class QurryV5:
    """Qurry V0.5.0
    The qiskit job tool
    """
    __version__ = (0, 5, 0)

    """ defaultConfig for single experiment. """

    @abstractmethod
    class argsCore(NamedTuple):
        """Construct the experiment's parameters."""

    class argsCore(NamedTuple):
        expsName: str = 'exps'
        wave: Union[QuantumCircuit, any, None] = None
        sampling: int = 1

    class argsMain(NamedTuple):
        # ID of experiment.
        expID: Optional[str] = None

        # Qiskit argument of experiment.
        # Multiple jobs shared
        shots: int = 1024
        backend: Backend = AerProvider().get_backend('aer_simulator')
        provider: Optional[AccountProvider] = None
        runArgs: dict[str, any] = {}

        # Single job dedicated
        runBy: str = "gate"
        decompose: Optional[int] = 2
        transpileArgs: dict[str, any] = {}

        # Other arguments of experiment
        drawMethod: str = 'text'
        resultKeep: bool = False
        tags: tuple[str] = ()
        resoureControl: dict[str, any] = {}

        saveLocation: Union[Path, str] = Path('./')
        exportLocation: Path = Path('./')

        expIndex: Optional[int] = None
        
    @abstractmethod
    class expsCore(NamedTuple):
        """Construct the experiment's output."""
    class expsCore(NamedTuple):
        ...

    class expsMain(NamedTuple):
        # Measurement result
        circuit: list[QuantumCircuit] = []
        figRaw: list[str] = []
        figTranspile: list[str] = []
        result: list[Result] = []
        counts: list[dict[str, int]] = []

        # Export data
        jobID: str = ''
        expsName: str = 'exps'

        # side product
        sideProduct: dict = {}

    _expsBaseExceptKeys = ['sideProduct', 'result']
    _v3ArgsMapping = {
        'runConfig': 'runArgs',
    }

    def expsBaseExcepts(
        self,
        excepts: list[str] = _expsBaseExceptKeys,
    ) -> dict:
        """The exception when export.

        Args:
            excepts (list[str], optional):
                Key of value wanted to be excluded.
                Defaults to ['sideProduct'].

        Returns:
            dict: The value will be excluded.
        """
        return self._expsBase.make(partial=excepts)

    """ defaultConfig for multiple experiments. """

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
    
    