from qiskit import QuantumCircuit
from qiskit.result import Result
from qiskit.providers import Backend
from qiskit.providers.ibmq import AccountProvider
from qiskit_aer import AerSimulator

from pathlib import Path
from typing import Literal, Union, Optional, NamedTuple, Hashable, overload
from abc import abstractmethod, abstractstaticmethod, abstractclassmethod
from collections import namedtuple
from uuid import uuid4
from datetime import datetime
import gc
import warnings

from ...mori import jsonablize, TagMap, syncControl
from ...mori.type import TagMapType
from ...exceptions import QurryInvalidInherition, QurryExperimentCountsNotCompleted
from ..declare.type import Quantity, Counts, waveGetter, waveReturn

class QurryMultiManager:

    class treatyparams(NamedTuple):
        """Multiple jobs shared. `argsMultiMain` in V4 format.
        """

        shots: int = 1024
        """Number of shots to run the program (default: 1024), which multiple experiments shared."""
        backend: Backend = AerSimulator()
        """Backend to execute the circuits on, which multiple experiments shared."""
        provider: Optional[AccountProvider] = None
        """Provider to execute the backend on, which multiple experiments shared."""

        managerRunArgs: dict[str, any] = None
        """Other arguments will be passed to `IBMQJobManager()`"""

        expsName: str = None
        saveLocation: Union[Path, str] = Path('./')
        """Location of saving experiment."""
        exportLocation: Path = Path('./')
        """Location of exporting experiment, exportLocation is the final result decided by experiment."""

        resoureControl: dict[str, any] = {}
        """Arguments of `ResoureWatch`."""
        pendingStrategy: Literal['power', 'tags', 'each'] = None
        jobsType: Literal["local", "IBMQ", "AWS_Bracket",
                          "Azure_Q", "multiJobs", "powerJobs"] = None
        clear: bool = None
        independentExports: list[str] = None
        filetype: TagMap._availableFileType = None

    class treatypreparation(NamedTuple):
        """`expsMultiMain` in V4 format."""

        powerJobID: Union[str, list[str]] = []
        gitignore: syncControl = syncControl()

        circuitsNum: dict[str, int] = {}
        state: Literal["init", "pending", "completed"] = 'init'

    class before(NamedTuple):
        """`dataNeccessary` and `expsMultiMain` in V4 format."""
        configDict: dict
        # with Job.json file
        tagMapExpsID: TagMapType[str]
        tagMapFiles: TagMapType[str]
        tagMapIndex: TagMapType[Union[str, int]]
        # circuitsMap
        circuitsMap: TagMapType[str]
        pendingPools: TagMapType[str]

    _v3ArgsMapping = {
        'circuitsMap': 'circuitsMap',
    }

    class after(NamedTuple):
        """`dataStateDepending` and `dataNeccessary` in V4 format."""
        tagMapQuantity: TagMapType[Quantity]
        tagMapCounts: TagMapType[Counts]

        tagMapResult: TagMapType[Result]

    _unexports = ['configList', 'tagMapResult']
    _exportsExceptKeys = ['configList']
    _powerJobKeyRequired = ['powerJobID', 'state']
    _multiJobKeyRequired = ['state']
    _independentExport = ['configDict']

    def __init__(self, *args, **kwargs) -> None:

        self.args = self.argsMultiMain(*args, **kwargs)
        self.exps = self.expsMultiMain()
        self.stateDepending = self.dataStateDepending()
        self.unexported = self.dataUnexported()
        self.neccessary = self.dataNeccessary()
