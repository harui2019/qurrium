from qiskit import (
    execute, transpile,
    QuantumRegister, ClassicalRegister, QuantumCircuit
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
    IBMQJobManagerInvalidStateError,
    IBMQJobManagerUnknownJobSet)

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

import numpy as np
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
from collections import Counter, namedtuple

from ..util import Gajima, ResoureWatch
from ..mori import (
    Configuration,
    attributedDict,
    defaultConfig,
    syncControl,
    jsonablize,
    quickJSONExport,
    keyTupleLoads,
    sortHashableAhead,
    TagMap,
)
from ..mori.type import TagMapType
from .exceptions import UnconfiguredWarning
from .type import (
    Quantity,
    Counts,
    waveGetter,
    waveReturn,
)

# Qurry V0.4.0 - a Qiskit Macro


def defaultCircuit(numQubit: int) -> QuantumCircuit:
    return QuantumCircuit(
        numQubit, numQubit, name=f'qurry_default_{numQubit}')


class QurryV4:
    """Qurry V0.4.0
    The qiskit job tool
    """
    __version__ = (0, 4, 0)

    """ Configuration for single experiment. """

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
        runArgs: dict = {}

        # Single job dedicated
        runBy: str = "gate"
        decompose: Optional[int] = 2
        transpileArgs: dict = {}

        # Other arguments of experiment
        drawMethod: str = 'text'
        resultKeep: bool = False
        tags: tuple[str] = ()

        saveLocation: Union[Path, str] = Path('./')
        exportLocation: Path = Path('./')

        expIndex: Optional[int] = None

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
        
    _v3ArgsMapping = {
        'runConfig': 'runArgs',
    }

    def expsBase(
        self,
        name: str = 'qurryExpsBase',
        defaultArg: dict = {
            # Arguments of experiment.
        },
    ) -> Configuration:
        """The default storage format and values of a single experiment.
        - Example:

        >>> self._expsBase = self.expsBase(
            name='dummyBase',
            defaultArg={
                'dummyResult1': None,
                'dummyResult2': None,
            },
        )

        Then :attr:`._expsBase` will be

        >>> {
            # Reault of experiment.
            'echo': -100,
            #
            # Measurement result
            'circuit': None,
            'figRaw': 'unexport',
            'figTranspile': 'unexport',
            'result': None,
            'counts': None,
            #
            # Export data
            'jobID': '',
            #
            'dummyResult1': None,
            'dummyResult2': None,
        }

        Args:
            name (str, optional):
                Name of basic configuration for `Qurry`.
                Defaults to 'qurryExpsBase'.
            expsConfig (dict, optional):
                `expsConfig`.
                Defaults to {}.
            defaultArg (dict, optional):
                Basic input for `.output`.
                Defaults to {}.

        Returns:
            Configuration: The template of experiment data.
        """
        return Configuration(
            name=name,
            default={
                **defaultArg,
                **self.argsMain()._asdict(),
                **self.argsCore()._asdict(),
                **self.expsMain()._asdict(),
            },
        )

    _expsBaseExceptKeys = ['sideProduct', 'result']
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

    """ Configuration for multiple experiments. """

    class argsMultiMain(NamedTuple):
        # Configuration of `IBMQJobManager().run`
        # Multiple jobs shared
        shots: int = 1024
        backend: Backend = AerProvider().get_backend('aer_simulator')
        provider: AccountProvider = None

        # IBMQJobManager() dedicated
        managerRunArgs: dict = {
            'max_experiments_per_job': 200,
        }
        powerJobID: Optional[str] = None

        # Other arguments of experiment
        # Multiple jobs shared
        expsName: str = 'exps'
        saveLocation: Union[Path, str] = Path('./')
        exportLocation: Path = Path('./')

        jobsType: Literal["multiJobs", "powerJobs"] = "multiJobs"
        isRetrieve: bool = False
        independentExports: list[str] = []
        filetype: TagMap._availableFileType = 'json'

    class expsMultiMain(NamedTuple):
        # configList
        configList: list = []

        gitignore: syncControl = syncControl()

        # independentExports
        tagMapQuantity: TagMapType[Quantity] = TagMap()
        tagMapCounts: TagMapType[Counts] = TagMap()
        # tagMapResult: TagMapType[Result] = TagMap()

        # with Job.json file
        tagMapExpsID: TagMapType[str] = TagMap()
        tagMapFiles: TagMapType[str] = TagMap()
        tagMapIndex: TagMapType[Union[str, int]] = TagMap()
        # circuitsMap: TagMapType[str] = TagMap()
        tagMapCircuits: TagMapType[str] = TagMap()
        circuitsNum: dict[str, int] = {}

        state: Literal["init", "pending", "completed"] = "init"
        
    _v3MultiArgsMapping = {
        'circuitsMap': 'tagMapCircuits',
    }

    def expsMultiBase(
        self,
        name: str = 'qurryMultiBase',
        defaultArg: dict = {
            # Arguments of experiment.
        },
    ) -> Configuration:
        """The default storage format and values of a single experiment.
        - Example:

        >>> self._expsMultiBase = self.expsMultiBase(
            name='dummyMultiBase',
            defaultArg={
                'dummyResult1': None,
                'dummyResult2': None,
            },
        )

        Then :attr:`._expsMultiMain` will be

        >>> {
            # configList
            configList: [],
            #
            gitignore: syncControl(),
            #
            # tagMapStateDepending
            tagMapQuantity: TagMap(),
            tagMapCounts: TagMap(),
            #
            # tagMapUnexported
            # tagMapResult: TagMap(),
            #
            # tagMapNeccessary
            tagMapExpsID: TagMap(),
            tagMapFiles: TagMap(),
            tagMapIndex: TagMap(),
            tagMapCircuits: TagMap(),
            circuitsNum: dict[str, int] = {}
            #
            state: Literal["init", "pending", "completed"] = "init"
            #
            'dummyResult1': None,
            'dummyResult2': None,
        }

        Args:
            name (str, optional):
                Name of basic configuration for `Qurry`.
                Defaults to 'qurryExpsBase'.
            expsConfig (dict, optional):
                `expsConfig`.
                Defaults to {}.
            defaultArg (dict, optional):
                Basic input for `.output`.
                Defaults to {}.

        Returns:
            Configuration: The template of experiment data.
        """
        return Configuration(
            name=name,
            default={
                **defaultArg,
                **self.argsMultiMain()._asdict(),
                **self.expsMultiMain()._asdict(),
            },
        )

    # TODO: make hint available in qurry

    def expsHint(
        self,
        name: str = 'qurryBaseHint',
        hintContext: dict = {
            "_basicHint": "This is a hint of QurryV4.",
        },
    ) -> dict:
        """Make hints for every values in :func:`.expsBase()`.
        - Example:

        >>> self._expsMultiBase = self.expsHint(
            name: str = 'qurryBaseHint',
            hintContext = {
                'expID': 'This is a expID'. # hint for `expsBase` value
                'dummyResult1': 'This is dummyResult1.', # extra hint
                'dummyResult2': 'This is dummyResult2.', # extra hint
            },
        )

        Then :attr:`.expHint` will be

        >>> {
            'expID': 'This is a expID',
            'shots': '', # value without hint
            ..., # other in `expsBase`
            #
            'dummyResult1': 'This is dummyResult1.', # extra hint
            'dummyResult2': 'This is dummyResult2.', # extra hint
        }

        Args:
            name (str, optional):
                Name of basic configuration for `Qurry`.
                Defaults to 'qurryBaseHint'.
            hintContext (dict, optional):
                Hints for `.expBase`.
                Defaults to `{
                    "_basicHint": "This is a hint of QurryV4.",
                }`.

        Returns:
            dict: The hints of the experiment data.
        """

        hintDefaults = {k: "" for k in self.expsBase()}
        hintDefaults = {**hintDefaults, **hintContext}
        
        return hintDefaults

    """ Initialize """

    @abstractmethod
    def initialize(self) -> dict[str, any]:
        """Configuration to Initialize QurryV4.

        Returns:
            dict[str, any]: The basic configuration of `Qurry`.
        """

    def initialize(self) -> dict[str, any]:

        self._expsBase = self.expsBase()
        self._expsHint = self.expsHint()
        self._expsMultiBase = self.expsMultiBase()
        self.shortName = 'qurry'
        self.__name__ = 'Qurry'

    jobManager = IBMQJobManager()

    def __init__(
        self,
        waves: Union[QuantumCircuit, list[QuantumCircuit]] = defaultCircuit(4),
    ) -> None:
        """The initialization of QurryV4.

        Args:
            waves (Union[QuantumCircuit, list[QuantumCircuit]], optional):
            The wave functions or circuits want to measure. Defaults to defaultCircuit.

        Raises:
            ValueError: When input is a null list.
            TypeError: When input is nor a `QuantumCircuit` or `list[QuantumCircuit]`.
            KeyError: Configuration lost.
            KeyError: `self.measureConfig['hint']` is not completed.
        """
        # basic check
        if hasattr(self, 'initialize'):
            self.initialize()
            for k in ['expsMultiBase', '_expsBase', '_expsHint', 'shortName']:
                if not hasattr(self, k):
                    raise AttributeError(
                        f"'{k}' is lost, initialization stop.")
        else:
            raise AttributeError(
                "'initialize' lost, this class could not be initialized.")

        # wave add
        if isinstance(waves, list):
            waveNums = len(waves)
            self.waves = {i: waves[i] for i in range(waveNums)}
            if waveNums == 0:
                raise ValueError(
                    "The list must have at least one wave function.")
        elif isinstance(waves, QuantumCircuit):
            self.waves = {0: waves}
        elif isinstance(waves, dict):
            self.waves = waves
        else:
            raise TypeError(
                f"Create '{self.__name__}' required a input as " +
                "'QuantumCircuit' or 'list[QuantumCircuit]'")
        self.lastWave = list(self.waves.keys())[-1]

        # value create
        self.exps = {}
        self.expsBelong = {}
        self.expsMulti = attributedDict(
            params=self.expsMultiMain()._asdict()
        )  # reresh per execution.

        # TODO: add params control
        self.resourceWatch = ResoureWatch()

        # namedtuple prototype
        self.namedtupleNow = namedtuple(
            typename='qurryArguments',
            field_names=self.argsMain._fields+self.argsCore._fields,
            defaults=list(self.argsMain._field_defaults.values())+list(self.argsCore._field_defaults.values()),
        )

        # For reading arguments.
        self.now: Union[QurryV4.argsMain, QurryV4.argsCore] = self.namedtupleNow(**{
            **self.argsCore()._asdict(), **self.argsMain()._asdict()
        })
        self.IDNow = ''
        self.multiNow: QurryV4.argsMultiMain = self.argsMultiMain()

    """Wave Function"""
    @staticmethod
    def decomposer(
        qc: QuantumCircuit,
        decompose: int = 2,
    ) -> QuantumCircuit:
        """Decompose the circuit with giving times.

        Args:
            qc (QuantumCircuit): The circuit wanted to be decomposed.
            decompose (int, optional):  Decide the times of decomposing the circuit.
                Draw quantum circuit with composed circuit. Defaults to 2.

        Returns:
            QuantumCircuit: The decomposed circuit.
        """

        qcResult = qc
        for t in range(decompose):
            qcResult = qcResult.decompose()
        return qcResult

    @overload
    def addWave(
        self,
        waveCircuit: list[QuantumCircuit],
        key=None,
    ) -> list[Optional[Hashable]]:
        ...

    @overload
    def addWave(
        self,
        waveCircuit: QuantumCircuit,
        key=None,
    ) -> Optional[Hashable]:
        ...

    def addWave(
        self,
        waveCircuit: Union[QuantumCircuit, list[QuantumCircuit]],
        key: Optional[waveGetter[Hashable]] = None,
        replace: Literal[True, False, 'duplicate'] = False,
    ):
        """Add new wave function to measure.

        Args:
            waveCircuit (Union[QuantumCircuit, list[QuantumCircuit]]): The wave functions or circuits want to measure.
            key (Optional[Hashable], optional): Given a specific key to add to the wave function or circuit,
                if `key == None`, then generate a number as key.
                Defaults to `None`.
            replace (bool, optional): 
                If the key is already in the wave function or circuit,
                then replace the old wave function or circuit when `True`,
                or duplicate the wave function or circuit when `'duplicate'`,
                otherwise only changes `.lastwave`.
                Defaults to `False`.

        Returns:
            Optional[Hashable]: Key of given wave function in `.waves`.
        """

        if isinstance(waveCircuit, QuantumCircuit):
            genKey = len(self.waves)
            if key == None:
                key = genKey
            elif not isinstance(key, Hashable):
                key = genKey

            if key in self.waves and replace == False:
                ...

            elif key in self.waves and replace == 'duplicate':
                while genKey in self.waves:
                    genKey += 1
                key = genKey
                self.waves[key] = waveCircuit

            else:
                self.waves[key] = waveCircuit

            self.lastWave = key
            return self.lastWave

        elif isinstance(waveCircuit, list):
            if isinstance(key, list):
                if len(key) == len(waveCircuit):
                    return [self.addWave(
                        waveCircuit=waveCircuit[i], key=key[i]) for i in range(len(waveCircuit))]
                else:
                    warnings.warn(
                        "The length of key is not equal to the length of waveCircuit, then replace by automatic generating.")
                    return [self.addWave(waveCircuit=waveCircuit[i])
                            for i in range(len(waveCircuit))]
            else:
                warnings.warn(
                    "The key is a list when waveCircuit is list, then replace by automatic generating.")
                return [self.addWave(waveCircuit=waveCircuit[i])
                        for i in range(len(waveCircuit))]

        else:
            warnings.warn("The input is not a 'QuantumCircuit'.")
            return None

    def hasWave(
        self,
        wavename: Hashable,
    ) -> bool:
        """Is there a wave with specific name.

        Args:
            wavename (Hashable): Name of wave which is used in `.waves`

        Returns:
            bool: Exist or not.
        """
        return wavename in self.waves

    def waveCall(
        self,
        wave: Union[list[Hashable], Hashable, None] = None,
        runBy: Optional[Literal['gate', 'operator',
                                'instruction', 'copy']] = None,
        backend: Optional[Backend] = AerProvider(
        ).get_backend('aer_simulator'),
    ) -> waveGetter[waveReturn]:
        """Parse wave Circuit into `Instruction` as `Gate` or `Operator` on `QuantumCircuit`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.
            runBy (Optional[str], optional):
                Export as `Gate`, `Operator`, `Instruction` or a copy when input is `None`.
                Defaults to `None`.
            backend (Optional[Backend], optional):
                Current backend which to check whether exports to `IBMQBacked`,
                if does, then no matter what option input at `runBy` will export `Gate`.
                Defaults to AerProvider().get_backend('aer_simulator').

        Returns:
            waveReturn: The result of the wave as `Gate` or `Operator`.
        """

        if wave == None:
            wave = self.lastWave
        elif isinstance(wave, list):
            return [self.waveCall(w, runBy, backend) for w in wave]

        if isinstance(backend, IBMQBackend):
            return self.waves[wave].to_instruction()
        elif runBy == 'operator':
            return Operator(self.waves[wave])
        elif runBy == 'gate':
            return self.waves[wave].to_gate()
        elif runBy == 'instruction':
            return self.waves[wave].to_instruction()
        elif runBy == 'copy':
            return self.waves[wave].copy()
        else:
            return self.waves[wave].to_gate()

    def waveOperator(
        self,
        wave: Optional[Hashable] = None,
    ) -> waveGetter[Operator]:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.waveCall(
            wave=wave,
            runBy='operator',
        )

    def waveGate(
        self,
        wave: Optional[Hashable] = None,
    ) -> waveGetter[Gate]:
        """Export wave function as `Gate`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.

        Returns:
            Gate: The gate of wave function.
        """
        return self.waveCall(
            wave=wave,
            runBy='gate',
        )

    def find(
        self,
        expID: Optional[str] = None,
    ) -> Optional[str]:
        """Check whether given `expID` is available,
        If does, then return it, otherwise return `False`.
        Or given current `expID` when doesn't give any id.

        Args:
            expID (Optional[str], optional): The `expID` wants to check. Defaults to None.

        Returns:
            str: The available `expID`.
        """

        if expID != None:
            tgtId = expID if expID in self.exps else None
        else:
            tgtId = self.IDNow

        return tgtId

    def drawWave(
        self,
        wave: Optional[Hashable] = None,
        drawMethod: Optional[str] = 'text',
        decompose: Optional[int] = 1,
    ) -> Figure:
        """Draw the circuit of wave function.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.
            drawMethod (Optional[str], optional): Draw quantum circuit by
                "text", "matplotlib", or "latex". Defaults to 'text'.
            decompose (Optional[int], optional): Draw quantum circuit with
                `QuantumCircuit` decomposed with given times. Defaults to 1.

        Returns:
            Union[str, Figure]: The figure of wave function.
        """
        if wave == None:
            wave = self.lastWave

        qDummy = QuantumRegister(self.waves[wave].num_qubits, 'q')
        qcDummy = QuantumCircuit(qDummy)

        qcDummy.append(self.waveGate(wave), [
            qDummy[i] for i in range(self.waves[wave].num_qubits)])
        qcDummy = self.decomposer(qcDummy, decompose)

        return qcDummy.draw(drawMethod)

    @abstractmethod
    def paramsControlCore(self) -> dict:
        """Control the experiment's parameters."""

    def paramsControlCore(
        self,
        expsName: str = 'exps',
        wave: Union[QuantumCircuit, any, None] = None,
        sampling: int = 1,
        **otherArgs: any
    ) -> dict:
        """Handling all arguments and initializing a single experiment.

        Args:
            wave (Union[QuantumCircuit, int, None], optional):
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
                Defaults to None.

            expsName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            otherArgs (any):
                Other arguments.

        Returns:
            dict: The export will be processed in `.paramsControlCore`
        """

        # wave
        if isinstance(wave, QuantumCircuit):
            wave = self.addWave(wave)
            print(f"| Add new wave with key: {wave}")
        elif wave == None:
            wave = self.lastWave
            print(f"| Autofill will use '.lastWave' as key")
        else:
            try:
                self.waves[wave]
            except KeyError as e:
                warnings.warn(f"'{e}', use '.lastWave' as key")
                wave = self.lastWave

        # sampling
        if isinstance(sampling, int):
            ...
        else:
            sampling = 1
            warnings.warn(f"'{sampling}' is not an integer, use 1 as default")

        return {
            'wave': wave,
            'expsName': f"{expsName}.{wave}",
            'sampling': sampling,
            **otherArgs,
        }

    def paramsControlMain(
        self,
        # ID of experiment.
        expID: Optional[str] = None,
        # Qiskit argument of experiment.
        # Multiple jobs shared
        shots: int = 1024,
        backend: Backend = AerProvider().get_backend('aer_simulator'),
        provider: Optional[AccountProvider] = None,
        runArgs: dict = {},
        # Single job dedicated
        runBy: str = "gate",
        decompose: Optional[int] = 2,
        transpileArgs: dict = {},
        # Other arguments of experiment
        drawMethod: str = 'text',
        resultKeep: bool = False,
        tags: Optional[Hashable] = None,

        **otherArgs: any,
    ) -> argsMain:
        """Handling all arguments and initializing a single experiment.

        - example of a value in `self.exps`

        ```
        {
            # ID of experiment.
            'expID': None,

            # Variants of experiment.
            **defaultArg,

            # Qiskit argument of experiment.
            # Multiple jobs shared
            'shots': 1024,
            'backend': AerProvider().get_backend('aer_simulator'),
            'runArgs': {},
            'expsName': 'exps',

            # Single job dedicated
            'runBy': "gate",
            'decompose': 1,
            'transpileArgs': {},

            # Other arguments of experiment
            'drawMethod': 'text',
            'resultKeep': False,
            'tags': tags,

            # Result of experiment.
            'echo': -100,

            # Measurement result
            'circuit': None,
            'figRaw': 'unexport',
            'figTranspile': 'unexport',
            'result': None,
            'counts': None,

            # Export data
            'jobID': '',
        }
        ```

        Args:
            # ID of experiment.

            expID (Optional[str], optional):
                Decide whether generate new id to initializw new experiment or continue current experiment.
                `True` for create new id.
                `False` for continuing current experiment.
                `None` will create new id automatically.
                Giving a key which exists in `.exps` will switch to this experiment to operate it.
                Default to `None`.

            # Qiskit argument of experiment.
            # Multiple jobs shared.

            shots (int, optional):
                Shots of the job.
                Defaults to `1024`.

            backend (Backend, optional):
                The quantum backend.
                Defaults to `AerProvider().get_backend('aer_simulator')`.

            provider (Optional[AccountProvider], optional):
                :cls:`AccountProvider` of current backend for running :cls:`IBMQJobManager`.
                Defaults to `None`.

            runArgs (dict, optional):
                Configuration of :func:`qiskit.execute`.
                Defaults to `{}`.

            # Single job dedicated

            runBy (str, optional):
                Construct wave function as initial state by :cls:`Operater` or :cls:`Gate`.
                When use 'IBMQBackend' only allowed to use wave function as `Gate` instead of `Operator`.
                Defaults to `"gate"`.

            decompose (Optional[int], optional):
                Running `QuantumCircuit` which be decomposed given times.
                Defaults to 2.

            transpileArg (dict, optional):
                Configuration of :func:`qiskit.transpile`.
                Defaults to `{}`.

            # Other arguments of experiment

            drawMethod (Optional[str], optional):
                Draw quantum circuit by `txt`, `matplotlib`, or `LaTeX`.
                Defaults to `'text'`.

            resultKeep (bool, optional):
                Whether to keep the results of qiskit job.
                Defaults to `False`.

            tags (Optional[Union[list[any], any]], optional):
                Given the experiment multiple tags to make a dictionary for recongnizing it.
                Defaults to `None`.

            otherArgs (any):
                Other arguments includes the variants of experiment.

        Raises:
            KeyError: Given `expID` does not exist.

        Returns:
            attributedDict: Current arguments.
        """

        # expID
        if expID is None or expID == '':
            self.IDNow = str(uuid4())
        elif expID in self.exps:
            self.IDNow = expID
        elif expID == False:
            ...
        else:
            raise KeyError(f"{expID} does not exist, '.IDNow' = {self.IDNow}.")

        # tags
        if tags in self.expsBelong:
            self.expsBelong[tags].append(self.IDNow)
        else:
            self.expsBelong[tags] = [self.IDNow]

        # TODO: add params control
        self.resourceWatch = ResoureWatch(
            **otherArgs
        )

        # Export all arguments
        coreFiltered  = self.paramsControlCore(**otherArgs)
        coreParams = {k: v for k, v in coreFiltered.items() if k in self.argsCore._fields}
        otherParams = {k: v for k, v in coreFiltered.items() if not k in self.argsCore._fields}

        self.now: Union[QurryV4.argsMain, QurryV4.argsCore] = self.namedtupleNow(**{
            # ID of experiment.
            'expID': self.IDNow,

            # Qiskit argument of experiment.
            # Multiple jobs shared
            'shots': shots,
            'backend': backend,
            'provider': provider,
            'runArgs': runArgs if not 'runConfig' in otherArgs else {
                **runArgs, **otherArgs['runConfig'],
            },

            # Single job dedicated
            'runBy': 'gate' if isinstance(backend, IBMQBackend) else runBy,
            'decompose': decompose,
            'transpileArgs': transpileArgs,

            # Other arguments of experiment
            'drawMethod': drawMethod,
            'resultKeep': resultKeep,
            'tags': tags,

            **coreParams
        })
        self.exps[self.IDNow] = {
            **otherParams,
            **self.now._asdict(),
            **self._expsBase.make(),
        }

        return self.now
    
    def drawCircuit(
        self,
        expID: Optional[str] = None,
        circuitSet: Optional[
            Union[QuantumCircuit, list[QuantumCircuit]]] = None,
        whichCircuit: int = 0,
        drawMethod: str = 'text',
        decompose: int = 0,
    ) -> Optional[Figure]:
        """Draw the circuit of wave function.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.
            whichCircuit (Optional[int], optional):
                If there is multiple circuits used in this experiment,
                then used the given number as index of list to pick up the circuit.
                and the first circuit which index is '0' as default export when not specified.
            drawMethod (Optional[str], optional): Draw quantum circuit by
                "text", "matplotlib", or "latex". Defaults to 'text'.
            decompose (Optional[int], optional): Draw quantum circuit with
                `QuantumCircuit` decomposed with given times. Defaults to 1.

        Returns:
            Union[str, Figure]: The figure of wave function.
        """

        if circuitSet:
            ...
        elif expID != None:
            tgtId = self.find(expID=expID)
            if tgtId:
                circuitSet = self.exps[tgtId]['circuit']
            else:
                warnings.warn(f"'{expID}' does not exist.")
                return None
        else:
            warnings.warn(f"'{circuitSet}' and '{expID}' are not available.")
            return None

        if isinstance(circuitSet, QuantumCircuit):
            circuit = self.decomposer(circuitSet, decompose)
            return circuit.draw(drawMethod)

        elif isinstance(circuitSet, list):
            circuit = self.decomposer(
                circuitSet[whichCircuit], decompose)
            return circuit.draw(drawMethod)

        else:
            warnings.warn(
                f"The type of '{circuitSet}' is '{type(circuitSet)}', which can not export.")
            return None

    @abstractmethod
    def method(self) -> list[QuantumCircuit]:
        """The method to construct circuit.
        Where should be overwritten by each construction of new measurement.

        Returns:
            Union[QuantumCircuit, list[QuantumCircuit]]:
                The quantum circuit of experiment.
        """

    def method(self) -> list[QuantumCircuit]:

        argsNow: Union[QurryV4.argsMain, QurryV4.argsCore] = self.now
        circuit = self.waves[argsNow.wave]
        numQubits = circuit.num_qubits
        print(
            f"| Directly call: {self.now.wave} with sampling {argsNow.sampling}")

        return [circuit for i in range(argsNow.sampling)]

    def build(
        self,
        **allArgs: any,
    ) -> list[QuantumCircuit]:
        """Construct the quantum circuit of experiment.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.
        Returns:
            QuantumCircuit: The quantum circuit of experiment.
        """
        argsNow = self.paramsControlMain(**allArgs)

        # circuit
        circuitSet = self.circuitMethod() if hasattr(
            self, 'circuitMethod') else self.method()
        self.exps[self.IDNow]['circuit'] = circuitSet

        # draw
        figRaw = None
        if isinstance(circuitSet, QuantumCircuit):
            figRaw = [self.drawCircuit(
                expID=self.IDNow,
                drawMethod=argsNow.drawMethod,
                decompose=argsNow.decompose,
            )]

        elif isinstance(circuitSet, list):
            circuitSetLength = len(circuitSet)
            figRaw = [self.drawCircuit(
                expID=self.IDNow,
                whichCircuit=i,
                drawMethod=argsNow.drawMethod,
                decompose=argsNow.decompose,
            ) for i in range(circuitSetLength)]

        self.exps[self.IDNow]['figRaw'] = figRaw

        return circuitSet

    def writeLegacy(
        self,
        expID: Optional[str] = None,
        saveLocation: Optional[Union[Path, str]] = None,
        excepts: list = [],
        _isMulti: bool = False,
    ) -> dict[str, any]:
        """Export the experiment data, if there is a previous export, then will overwrite.

        - example of file.name:

            >>> {name}.{self.exps[expID]['expsName']}.expId={expID}.json

            In `self.exps`,
            >>> filename = ((
                Path(f"{self.exps[legacyId]['expsName']}.expId={legacyId}.json")
            )
            >>> self.exps[legacyId]['filename'] = filename

        Args:
            expID (Optional[str], optional):
                The id of the experiment will be exported.
                If `expID == None`, then export the experiment which id is`.IDNow`.
                Defaults to `None`.

            saveLocation (Optional[Union[Path, str]], optional):
                Where to save the export content as `json` file.
                If `saveLocation == None`, then cancelled the file to be exported.
                Defaults to `None`.

            name (str, optional):
                The first name of the file.
                Export as showing in example.

        Returns:
            dict[any]: the export content.
        """

        legacyId = self.find(expID)
        if legacyId == None:
            warnings.warn(
                f"No such expID '{expID}', waiting for legacy be written.")
            return {}

        # filename
        filename = f"{self.exps[legacyId]['expsName']}.expId={legacyId}"
        self.exps[legacyId]['filename'] = filename

        # filter
        if not isinstance(excepts, list):
            excepts = []
            warnings.warn(
                f"Type of 'excepts' is not 'list' instead of '{type(excepts)}', ignore exception.")
        exports = {
            k: self.exps[legacyId][k] for k in self.exps[legacyId]
            if k not in list(self.expsBaseExcepts().keys())+excepts
        }
        exports = sortHashableAhead(exports)

        with Gajima(
            prefix="| ",
            desc="Writing Legacy",
            finish_desc="Legacy write out.",
        ) as gajima:
            if isinstance(saveLocation, (Path, str)):
                saveLocParts = Path(saveLocation).parts
                saveLoc = Path(saveLocParts[0]) if len(
                    saveLocParts) > 0 else Path('./')
                for p in saveLocParts[1:]:
                    saveLoc /= p

                if _isMulti:
                    saveLoc = saveLoc / 'legacy'

                if not os.path.exists(saveLoc):
                    os.mkdir(saveLoc)

                self.exps[legacyId]['saveLocation'] = saveLoc
                legacyExport = jsonablize(exports)
                with open((saveLoc / (filename+'.json')), 'w+', encoding='utf-8') as Legacy:
                    json.dump(
                        legacyExport, Legacy, indent=2, ensure_ascii=False)

            else:
                legacyExport = jsonablize(exports)
                if saveLocation != None:
                    warnings.warn(
                        "'saveLocation' is not the type of 'str' or 'Path', " +
                        "so export cancelled.")

        tales = self.exps[legacyId]['sideProduct']
        if len(tales) > 0:
            with Gajima(
                prefix="| ",
                desc="Writing Tales",
                leave=False,
                finish_desc="Tales write out.",
            ) as gajima:
                talesLib = saveLoc / 'tales'
                if not os.path.exists(talesLib):
                    os.mkdir(talesLib)

                for k in tales:
                    talesExport = jsonablize(tales[k])
                    with open((talesLib / (filename+f'.{k}.json')), 'w+', encoding='utf-8') as Tales:
                        json.dump(
                            talesExport, Tales, indent=2, ensure_ascii=False)

        return legacyExport

    def readLegacy(
        self,
        expID: Optional[str] = None,
        filename: Optional[Union[Path, str]] = None,
        saveLocation: Union[Path, str] = Path('./'),
        excepts: list = [],
        _isMulti: bool = False,
    ) -> dict[str, any]:
        """Read the experiment data.

        Args:
            expID (Optional[str], optional):
                The id of the experiment will be exported.
                If `expID == None`, then export the experiment which id is`.IDNow`.
                Defaults to `None`.

            saveLocation (Optional[Union[Path, str]], optional):
                Where to save the export content as `json` file.
                If `saveLocation == None`, then cancelled the file to be exported.
                Defaults to `None`.

        Raises:
            ValueError: 'saveLocation' needs to be the type of 'str' or 'Path'.
            FileNotFoundError: When `saveLocation` is not available.
            FileNotFoundError: When the export of `expId` does not exist.
            TypeError: File content is not `dict`.

        Returns:
            dict[str, any]: The data.
        """

        if isinstance(saveLocation, (Path, str)):
            saveLocation = Path(saveLocation)
        else:
            raise ValueError(
                "'saveLocation' needs to be the type of 'str' or 'Path'.")

        if _isMulti:
            saveLocationLegacy = saveLocation / 'legacy'
            if os.path.exists(saveLocationLegacy):
                saveLocation = saveLocationLegacy
            else:
                print(f"| QurryV3 data readed.")

        legacyRead = {}
        if expID != None:
            lsfolder = glob.glob(str(saveLocation / f"*{expID}*.json"))
            if len(lsfolder) == 0:
                raise FileNotFoundError(
                    f"The file 'expID={expID}' not found at '{saveLocation}'.")

            for p in lsfolder:
                with open(p, 'r', encoding='utf-8') as Legacy:
                    legacyRead = json.load(Legacy)

        elif isinstance(filename, (str, Path)):
            if os.path.exists(saveLocation / filename):
                with open(saveLocation / filename, 'r', encoding='utf-8') as Legacy:
                    legacyRead = json.load(Legacy)

            else:
                print(f"'{(saveLocation / filename)}' does not exist.")

        else:
            raise FileNotFoundError(f"The file 'expID={expID}' not found.")

        legacyRead = {
            **self.expsBaseExcepts(),
            **{k: v for k, v in legacyRead.items() if k not in excepts},
        }
        
        # handle v3 compatibility
        for k in list(legacyRead):
            if k in self._v3ArgsMapping:
                legacyRead[self._v3ArgsMapping[k]] = legacyRead[k]

        if isinstance(legacyRead, dict):
            if "tags" in legacyRead:
                legacyRead["tags"] = tuple(legacyRead["tags"]) if isinstance(
                    legacyRead["tags"], list) else legacyRead["tags"]

            if not self._expsBase.ready(legacyRead, ignores=self._expsBaseExceptKeys):
                lost = self._expsBase.check(legacyRead, ignores=self._expsBaseExceptKeys)
                print(f"Key Lost: {lost}")
        else:
            raise TypeError("The export file does not match the type 'dict'.")

        return legacyRead

    def transpiler(
        self,
        **allArgs: any,
    ) -> list[QuantumCircuit]:
        """Export the job of experiments.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.

        Returns:
            list[QuantumCircuit]:
                Transpiled Circuit.
        """
        circuitSet = self.build(**allArgs)
        argsNow = self.now

        gajima = Gajima(
            prefix="| ",
            desc="Transpile circuits",
            finish_desc="Transpile finished",
        )
        gajima.run()
        # transpile
        circs = transpile(
            circuitSet if isinstance(circuitSet, list) else [circuitSet],
            backend=argsNow.backend,
            **argsNow.transpileArgs,
        )
        gajima.stop()

        figTranspile = []
        if isinstance(circs, QuantumCircuit):
            figTranspile.append(self.drawCircuit(
                expID=None,
                circuitSet=circs,
                drawMethod=argsNow.drawMethod,
                decompose=argsNow.decompose,
            ))

        elif isinstance(circs, list):
            for i, v in enumerate(circs):
                figTranspile.append(self.drawCircuit(
                    expID=None,
                    circuitSet=circs,
                    whichCircuit=i,
                    drawMethod=argsNow.drawMethod,
                    decompose=argsNow.decompose,
                ))
                

        else:
            raise TypeError(f"Unknown type '{type(circs)}'")

        self.exps[self.IDNow]['figTranspile'] = figTranspile
        return circs

    """ Execution single """

    def run(
        self,
        **allArgs: any,
    ) -> Result:
        """Export the result after running the job.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.

        Returns:
            Result: The result of the job.
        """
        circs = self.transpiler(**allArgs)
        argsNow = self.now

        execution = execute(
            circs,
            **argsNow.runArgs,
            backend=argsNow.backend,
            shots=argsNow.shots,
        )
        jobID = execution.job_id()
        self.exps[self.IDNow]['jobID'] = jobID
        date = datetime.datetime.today().strftime("%Y-%m-%d_%H-%M-%S")
        self.exps[self.IDNow]['dateCreate'] = date
        result = execution.result()
        self.exps[self.IDNow]['result'] = result

        return result

    """ Result processing """

    @abstractclassmethod
    def counts(cls) -> list[Counts]:
        """Get counts.
        Where should be overwritten by each construction of new measurement.

        Returns:
            Counts: Counts of experiment.
        """

    @classmethod
    def counts(
        cls,
        result: Union[Result, ManagedResults],
        resultIdxList: Optional[list[int]] = None,
        num: int = 1,
        **otherArgs,
    ):
        """Computing specific squantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            tuple[dict, dict]:
                Counts, purity, entropy of experiment.
        """
        if resultIdxList == None:
            resultIdxList = [i for i in range(num)]
        else:
            ...

        counts = []
        for i in resultIdxList:
            try:
                allMeas = result.get_counts(i)
                counts.append(allMeas)
            except IBMQManagedResultDataNotAvailable as err:
                counts.append({})
                print("| Failed Job result skip, index:", i, err)
                continue

        return counts

    @abstractclassmethod
    def quantities(cls) -> dict[str, float]:
        """Computing specific squantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            dict[str, float]: Counts, purity, entropy of experiment.
        """

    @classmethod
    def quantities(
        cls,
        shots: int,
        counts: list[Counts],
        num: int = 1,
        run_log: dict[str] = {},
        **otherArgs,
    ):

        dummy = -100
        quantity = {
            '_dummy': dummy,
            'sampling': num,
            **run_log,
        }
        return quantity

    """ Output single """

    def output(
        self,
        withCounts: bool = False,
        run_log: dict[str] = {},
        **allArgs: any,
    ) -> Union[Quantity, tuple[Quantity, Counts]]:
        """Export the result which completed calculating purity.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.

        Returns:
            dict[float]: The result.
        """
        print(f"+"+"-"*20+"\n"+f"| Calculating {self.__name__}...")
        result = self.run(**allArgs,)
        
        argsNow: Union[QurryV4.argsMain, QurryV4.argsCore] = self.now
        print(f"| name: {argsNow.expsName}\n"+f"| id: {self.IDNow}")
        
        counts = self.counts(
            **argsNow._asdict(),
            result=result,
        )

        quantity = self.quantities(
            **argsNow._asdict(),
            counts=counts,
        )

        if argsNow.resultKeep:
            warnings.warn(
                "Result will keep, but it may cause memory overallocated.")
            self.exps[self.IDNow]['result'] = result

        else:
            del self.exps[self.IDNow]['result']

        for k in quantity:
            if k[0] == '_' and k != '_dummy':
                self.exps[self.IDNow]['sideProduct'][k[1:]] = quantity[k]
            if k == '_dummy':
                withCounts = True

        for k, v in run_log.items():
            self.exps[self.IDNow]['sideProduct'][k] = v

        quantity = {k: quantity[k] for k in quantity if k[0] != '_'}
        self.exps[self.IDNow] = {
            **self.exps[self.IDNow],
            **quantity,
            'counts': counts,
        }

        gc.collect()
        print(f"| End...\n"+f"+"+"-"*20)

        return (quantity, counts) if withCounts else quantity

    @abstractmethod
    def measure(self) -> Union[Quantity, tuple[Quantity, Counts]]:
        """Computing specific squantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            tuple[dict, dict]:
                Counts, purity, entropy of experiment.
        """
        ...

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        expsName: str = 'exps',
        withCounts: bool = False,
        **otherArgs: any
    ):
        """

        Args:
            wave (Union[QuantumCircuit, int, None], optional):
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
                Defaults to None.

            expsName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            otherArgs (any):
                Other arguments.

        Returns:
            dict: The output.
        """

        warnings.warn(
            "This function is not yet configured with not completed function.",
            UnconfiguredWarning
        )

        return self.output(
            wave=wave,
            expsName=expsName,
            withCounts=withCounts,
            **otherArgs,
        )

    """ Execution Multiple """

    def resourceCheck(self) -> None:
        """_summary_
        """
        self.resourceWatch()
        self.resourceWatch.report()

    @classmethod
    def pending(
        cls,
        experiments: list,
        backend: Backend,
        shots: int = 1024,
        name: str = 'qurryV4',
        **managerRunArgs,
    ) -> dict[str, Union[ManagedJobSet, str]]:
        """_summary_

        Args:
            experiments (list): _description_
            backend (Backend): _description_
            shots (int, optional): _description_. Defaults to 1024.
            name (str, optional): _description_. Defaults to 'qurryV4'.

        Returns:
            dict[str, str]: _description_
        """

        pendingJob = cls.jobManager.run(
            **managerRunArgs,
            experiments=experiments,
            backend=backend,
            shots=shots,
            name=name,
        )
        jobID = pendingJob.job_set_id()
        report = pendingJob.report()

        return {
            'pendingJob': pendingJob,
            'jobID': jobID,
            'report': report,
        }

    @classmethod
    def retrieve(
        cls,
        jobID: str,
        provider: AccountProvider,
        refresh: bool = False,
    ) -> dict[str, Union[ManagedJobSet, str]]:
        """_summary_

        Args:
            jobID (str): _description_
            provider (AccountProvider): _description_
            refresh (bool, optional): _description_. Defaults to False.

        Returns:
            ManagedResults: _description_
        """

        retrievedJob = cls.jobManager.retrieve_job_set(
            job_set_id=jobID,
            provider=provider,
            refresh=refresh,
        )

        return {
            'retrievedJob': retrievedJob,
        }
        
    _time_ndigits = 2

    def _time_takes(
        self,
        start: float,
    ):
        return " - "+f"{round(time.time() - start, self._time_ndigits)}".rjust(4, '0')+" sec"

    _indexRename = 1
    _rjustLen = 3

    class _namingComplex(NamedTuple):
        expsName: str
        saveLocation: Path
        exportLocation: Path

    def _multiNaming(
        self,
        isRead: bool = False,
        expsName: str = 'exps',
        saveLocation: Union[Path, str] = Path('./'),
    ) -> _namingComplex:
        """The process of naming.

        Args:
            isRead (bool, optional): 
                Whether to read the experiment data.
                Defaults to False.

            expsName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            saveLocation (Union[Path, str], optional):
                Where to save the export data. Defaults to Path('./')

        Raises:
            TypeError: The :arg:`saveLocation` is not a 'str' or 'Path'.
            FileNotFoundError: The :arg:`saveLocation` is not existed.
            FileNotFoundError: Can not find the exportation data which will be readed.

        Returns:
            dict[str, Union[str, Path]]: Name.
        """

        print(f"| Naming...")
        if isinstance(saveLocation, (Path, str)):
            saveLocation = Path(saveLocation)
        else:
            raise TypeError(
                f"The saveLocation '{saveLocation}' is not the type of 'str' or 'Path' but '{type(saveLocation)}'.")

        if not os.path.exists(saveLocation):
            raise FileNotFoundError(
                f"Such location not found: '{saveLocation}'.")

        if isRead:
            immutableName = expsName
            exportLocation = saveLocation / immutableName
            if not os.path.exists(exportLocation):
                raise FileNotFoundError(
                    f"Such exportation data '{immutableName}' not found at '{saveLocation}', " +
                    "'exportsName' may be wrong or not in this folder.")
            print(
                f"| Retrieve {immutableName}...\n" +
                f"| at: {exportLocation}"
            )

        else:
            expsName = f'{expsName}.{self.shortName}'
            indexRename = self._indexRename

            immutableName = f"{expsName}.{str(indexRename).rjust(self._rjustLen, '0')}"
            exportLocation = saveLocation / immutableName
            while os.path.exists(exportLocation):
                print(f"| {exportLocation} is repeat location.")
                indexRename += 1
                immutableName = f"{expsName}.{str(indexRename).rjust(self._rjustLen, '0')}"
                exportLocation = saveLocation / immutableName
            print(
                f"| Write {immutableName}...\n" +
                f"| at: {exportLocation}"
            )
            os.makedirs(exportLocation)

        namingComplex = self._namingComplex(**{
            'expsName': immutableName,
            'saveLocation': saveLocation,
            'exportLocation': exportLocation,
        })

        return namingComplex

    _generalJobKeyRequired = ['state']
    _powerJobKeyRequired = ['powerJobID'] + _generalJobKeyRequired
    _multiJobKeyRequired = [] + _generalJobKeyRequired

    class _tagMapStateDepending(NamedTuple):
        tagMapQuantity: TagMapType[Quantity] = TagMap()
        tagMapCounts: TagMapType[Counts] = TagMap()

    class _tagMapUnexported(NamedTuple):
        tagMapResult: TagMapType[Result] = TagMap()

    class _tagMapNeccessary(NamedTuple):
        # with Job.json file
        tagMapExpsID: TagMapType[str] = TagMap()
        tagMapFiles: TagMapType[str] = TagMap()
        tagMapIndex: TagMapType[Union[str, int]] = TagMap()
        # circuitsMap
        tagMapCircuits: TagMapType[str] = TagMap()

    def _multiDataGenOrRead(
        self,
        namingComplex: _namingComplex,
        isRead: bool = False,
    ) -> tuple[
        _tagMapStateDepending,
        _tagMapUnexported,
        _tagMapNeccessary,
        dict[str, int],
        syncControl
    ]:
        """The process of data generation or reading.

        >>> class _tagMapStateDepending(NamedTuple):
                tagMapQuantity: TagMapType[Quantity] = TagMap()
                tagMapCounts: TagMapType[Counts] = TagMap()

        >>> class _tagMapUnexported(NamedTuple):
                tagMapResult: TagMapType[Result] = TagMap()

        >>> class _tagMapNeccessary(NamedTuple):
                # with Job.json file
                tagMapExpsID: TagMapType[str] = TagMap()
                tagMapFiles: TagMapType[str] = TagMap()
                tagMapIndex: TagMapType[Union[str, int]] = TagMap()
                # circuitsMap
                tagMapCircuits: TagMapType[str] = TagMap()

        Args:
            namingComplex (_namingComplex): 
                The namedtuple of names.
                >>> class _namingComplex(NamedTuple):
                        expsName: str
                        saveLocation: Path
                        exportLocation: Path

            isRead (bool, optional): 
                Is reading mode. Defaults to False.

        Raises:
            ValueError: The imported file broken.

        Returns:
            tuple[ _tagMapStateDepending, _tagMapUnexported, _tagMapNeccessary, dict[str, int], syncControl ]: _description_
        """

        if isRead:
            dataDummyJobs: dict[any] = {}
            dataPowerJobsName = namingComplex.exportLocation / \
                f"{namingComplex.expsName}.multiJobs.json"
            dataMultiJobsName = namingComplex.exportLocation / \
                f"{namingComplex.expsName}.powerJobs.json"

            # read
            if os.path.exists(dataPowerJobsName):
                with open(dataPowerJobsName, 'r', encoding='utf-8') as theData:
                    dataDummyJobs = json.load(theData)
                jobsType = "powerJobs"

            else:
                with open(dataMultiJobsName, 'r', encoding='utf-8') as theData:
                    dataDummyJobs = json.load(theData)
                jobsType = "multiJobs"

            # key check
            lostKey = []
            for k in (self._powerJobKeyRequired if jobsType == "powerJobs" else self._multiJobKeyRequired):
                if k not in dataDummyJobs:
                    lostKey.append(k)
            if len(lostKey) > 0:
                raise ValueError(
                    f"'{lostKey}' are the key required in 'powerJob', otherwise this file may be broken.")

            # state check
            if 'state' in dataDummyJobs:
                state = dataDummyJobs['state']
            else:
                warnings.warn(f"'state' no found, use '{state}'.")

            # handle v3 key name and value redefined
            for k in list(dataDummyJobs):
                if k in self._v3MultiArgsMapping:
                    dataDummyJobs[self._v3MultiArgsMapping[k]] = dataDummyJobs[k]
            if "independentExports" in dataDummyJobs:
                dataDummyJobs["independentExports"] = [
                    'tagMapQuantity', 'tagMapCounts', 'tagMapResult'],
            if 'listFile' in dataDummyJobs:
                dataDummyJobs['tagMapFiles'] = {
                    'noTags': dataDummyJobs['listFile']}

            # tagMapStateDepending
            if state == 'completed':
                tagMapStateDepending = self._tagMapStateDepending(
                    tagMapQuantity=TagMap.read(
                        saveLocation=namingComplex.exportLocation,
                        tagmapName='tagMapQuantity',
                    ),
                    tagMapCounts=TagMap.read(
                        saveLocation=namingComplex.exportLocation,
                        tagmapName='tagMapCounts',
                    )
                )
            else:
                tagMapStateDepending = self._tagMapStateDepending()

            # tagMapUnexported
            tagMapUnexported = self._tagMapUnexported()
            # tagMapNeccessary
            tagMapNeccessary = self._tagMapNeccessary(**{
                k: TagMap(dataDummyJobs[k]) if k in dataDummyJobs else TagMap.read(
                    saveLocation=namingComplex.saveLocation,
                    tagmapName=k,
                )
                for k in self._tagMapNeccessary._fields})

            circuitsNum: dict[str, int] = dataDummyJobs['circuitsNum']
            gitignore: syncControl = (syncControl(
                dataDummyJobs['gitignore']) if 'gitignore' in dataDummyJobs else syncControl())

        else:
            # tagMapStateDepending
            tagMapStateDepending = self._tagMapStateDepending()
            # tagMapUnexported
            tagMapUnexported = self._tagMapUnexported()
            # tagMapUnexported
            tagMapNeccessary = self._tagMapNeccessary()

            circuitsNum: dict[str, int] = {}
            gitignore: syncControl = syncControl()

        # reading experiment datas
        if isRead:
            for tags, files in tagMapNeccessary.tagMapExpsID.items():
                for expIDKey in files:
                    self.exps[expIDKey] = self.readLegacy(
                        expID=expIDKey,
                        saveLocation=Path(namingComplex.exportLocation),
                        _isMulti=True,
                    )

        return (
            tagMapStateDepending,
            tagMapUnexported,
            tagMapNeccessary,
            circuitsNum,
            gitignore,
        )

    def paramsControlMulti(
        self,
        # configList
        configList: list = [],

        # Configuration of `IBMQJobManager().run`
        # Multiple jobs shared
        shots: int = 1024,
        backend: Backend = AerProvider().get_backend('aer_simulator'),
        provider: AccountProvider = None,
        # IBMQJobManager() dedicated
        managerRunArgs: dict[str] = {
            'max_experiments_per_job': 200,
        },
        powerJobID: Optional[Union[str, list[str]]] = None,
        # Other arguments of experiment
        # Multiple jobs shared
        expsName: str = 'exps',
        saveLocation: Union[Path, str] = Path('./'),

        jobsType: Literal["multiJobs", "powerJobs"] = "multiJobs",
        isRetrieve: bool = False,
        isRead: bool = False,
        independentExports: list[str] = [
            'tagMapQuantity', 'tagMapCounts', 'tagMapResult'],

        # storage
        # gitignore: syncControl = syncControl(),
        # # independentExports
        # tagMapQuantity: TagMapType[Quantity] = TagMap(),
        # tagMapCounts: TagMapType[Counts] = TagMap(),
        # # tagMapResult: TagMapType[Result] = TagMap(),

        # # with Job.json file
        # tagMapExpsID: TagMapType[str] = TagMap(),
        # tagMapFiles: TagMapType[str] = TagMap(),
        # tagMapIndex: TagMapType[Union[str, int]] = TagMap(),
        # # circuitsMap: TagMapType[str] = TagMap(),
        # tagMapCircuits: TagMapType[str] = TagMap(),
        # circuitsNum: dict[str, int] = {},

        state: Literal["init", "pending", "completed"] = "init",

        **otherArgs: any,
    ) -> Union[argsMultiMain, expsMultiMain]:
        """Handling all arguments and initializing a single experiment.

        - example of a value in `self.exps`

        ```
        {
            # configList
            'configList': [],

            # Configuration of `IBMQJobManager().run`
            # Multiple jobs shared
            'shots': 1024,
            'backend': AerProvider().get_backend('aer_simulator'),
            'provider': 'None',
            'runConfig': {},

            # IBMQJobManager() dedicated
            'powerJobID': None,
            'managerRunArgs': {
                'max_experiments_per_job': 200,
            },

            # Other arguments of experiment
            # Multiple jobs shared
            'isRetrieve': False,
            'expsName': 'exps',

            # Multiple job dedicated
            'independentExports': False,

            # `writeLegacy`
            'saveLocation': None,
            'exportLocation': None,
        }
        ```

        Args:
            # List of experiments.

            configList (list):
                The list of configuration of multiple experiment.

            # Configuration of `IBMQJobManager().run`
            # Multiple jobs shared

            shots (int, optional):
                Shots of the job.
                Defaults to `1024`.

            backend (Backend, optional):
                The quantum backend.
                Defaults to `AerProvider().get_backend('aer_simulator')`.

            provider (Optional[AccountProvider], optional):
                :cls:`AccountProvider` of current backend for running :cls:`IBMQJobManager`.
                Defaults to `None`.

            # IBMQJobManager() dedicated
            managerRunArgs (dict, optional):
                Configuration of :func:`IBMQJobManager().run`.
                Defaults to `{
                    'max_experiments_per_job': 200,
                }`.

            expsName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            saveLocation (Union[Path, str], optional):
                Where to save the export data. Defaults to Path('./')

            # Other arguments of experiment
            jobType (str, optional):
                The type name of the jobs.
                Defaults to `"multiJobs"`.

            isRead (bool, optional): 
                Whether to read the experiment data.
                Defaults to False.

            isRetrieve (bool, optional):
                Whether to retrieve the experiment data.
                Defaults to `False`.

            independentExports (list[str], optional):
                Making independent output for some data will export in `multiJobs` or `powerJobs`.
                Defaults to `False`.


        - example of file.name:

            `{name}.{self.exps[expID]['expsName']}.expId={expID}.json`

            otherArgs (any):
                Other arguments includes the variants of experiment.

        Returns:
            attributedDict: Current arguments.
        """

        # is reading
        isRead = isRetrieve | isRead

        # naming
        namingComplex = self._multiNaming(
            isRead=isRead,
            expsName=expsName,
            saveLocation=saveLocation,
        )

        # configList
        initedConfigList = []
        for expIndex, config in enumerate(configList):
            initedConfigList.append({
                **config,
                'shots': shots,
                'backend': backend,
                'provider': provider,

                'expsName': namingComplex.expsName,
                'saveLocation': namingComplex.saveLocation,
                'exportLocation': namingComplex.exportLocation,

                'expIndex': expIndex,
            })

        # read or generate
        (
            tagMapStateDepending,
            tagMapUnexported,
            tagMapNeccessary,
            circuitsNum,
            gitignore
        ) = self._multiDataGenOrRead(
            namingComplex=namingComplex,
            isRead=isRead,
        )

        # powerJobID and handle v3
        if isinstance(powerJobID, str):
            powerJobID = [powerJobID]
        elif powerJobID is None:
            powerJobID = []
        elif isinstance(powerJobID, list):
            ...
        else:
            raise TypeError(
                f"Invalid type '{type(powerJobID)}' for 'powerJobID', only 'str', 'list[str]', or 'None' are available.")

        self.multiNow: QurryV4.argsMultiMain = self.argsMultiMain(**{
            # Configuration of `IBMQJobManager().run`
            # Multiple jobs shared
            'shots': shots,
            'backend': backend,
            'provider': provider,

            # IBMQJobManager() dedicated
            'managerRunArgs': managerRunArgs,
            'powerJobID': powerJobID,

            # Other arguments of experiment
            # Multiple jobs shared
            'expsName': namingComplex.expsName,
            'saveLocation': namingComplex.saveLocation,
            'exportLocation': namingComplex.exportLocation,

            'jobsType': jobsType,
            'isRetrieve': isRetrieve,
            'independentExports': independentExports,
        })
        self.expsMulti: QurryV4.expsMultiMain = attributedDict(
            params={
                **self.multiNow._asdict(),
                'state': state,

                # configList
                'configList': initedConfigList,

                'circuitsNum': circuitsNum,
                'gitignore': gitignore,

                # tagMapStateDepending
                **tagMapStateDepending._asdict(),
                # tagMapUnexported
                **tagMapUnexported._asdict(),
                # tagMapNeccessary
                **tagMapNeccessary._asdict(),

                **otherArgs,
            }
        )

        return self.expsMulti

    def multiRead(
        self,
        exportName: Union[Path, str],
        saveLocation: Union[Path, str] = './',
        isRetrieve: bool = False,
        **allArgs: any,
    ) -> dict[any]:
        """Require to read the file exported by `.powerJobsPending`.

        Args:
            exportName (Union[Path, str]):
                The folder name of the job wanted to import.


            powerJobID (str, optional):
                Job Id. Defaults to ''.

            provider (Optional[AccountProvider], optional):
                :cls:`AccountProvider` of current backend for running :cls:`IBMQJobManager`.
                Defaults to `None`.

            saveLocation (Optional[Union[Path, str]], optional):
                Where to save the export content as `json` file.
                If `saveLocation == None`, then cancelled the file to be exported.
                Defaults to `None`.

            allArgs: all arguments will handle by `.paramsControlMulti()` and export as specific format.

        Raises:
            ValueError: When file is broken.

        Returns:
            dict[any]: All result of jobs.
        """

        expsMulti = self.paramsControlMulti(
            saveLocation=saveLocation,
            expsName=exportName,
            isRead=True,
            isRetrieve=isRetrieve,
            **allArgs,
        )

        return expsMulti

    def multiOutput(
        self,
        # configList
        configList: list = [],

        # Configuration of `IBMQJobManager().run`
        # Multiple jobs shared
        shots: int = 1024,
        backend: Backend = AerProvider().get_backend('aer_simulator'),

        # Multiple jobs shared
        expsName: str = 'exps',
        saveLocation: Union[Path, str] = Path('./'),

        **allArgs: any,
    ) -> dict[any]:
        """Make multiple jobs output.

        Args:        
            configList (list):
                The list of configuration of multiple experiment.

            shots (int, optional):
                Shots of the job.
                Defaults to `1024`.

            backend (Backend, optional):
                The quantum backend.
                Defaults to `AerProvider().get_backend('aer_simulator')`.

            # Other arguments of experiment
            isRetrieve (bool, optional):
                Whether to retrieve the experiment date.
                Defaults to `False`.

            expsName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            independentExports (bool, optional):
                Making independent output for some data will export in `multiJobs` or `powerJobs`.
                Defaults to `False`.

            saveLocation (Optional[Union[Path, str]], optional):
                Where to save the export content as `json` file.
                If `saveLocation == None`, then cancelled the file to be exported.
                Defaults to `None`.

            name (str, optional):
                The first name of the file.
                Export as showing in example.

            allArgs: all arguments will handle by `.paramsControlMulti()` and export as specific format.

        Returns:
            dict[any]: All result of jobs.
        """
        start_time = time.time()
        expsMulti = self.paramsControlMulti(
            configList=configList,
            # Configuration of `IBMQJobManager().run`
            # Multiple jobs shared
            shots=shots,
            backend=backend,
            # Other arguments of experiment
            # Multiple jobs shared
            expsName=expsName,
            saveLocation=saveLocation,

            jobsType='multiJobs',
            isRetrieve=False,
            isRead=False,
            **allArgs
        )

        print(f"| MultiOutput {self.__name__} Start...\n"+f"+"+"-"*20)
        numConfig = len(self.expsMulti.configList)
        for config in expsMulti.configList:
            print(
                f"| index={config['expIndex']}/{numConfig} - {self._time_takes(start_time)}.")
            quantity, counts = self.output(
                **config,
                withCounts=True,
                run_log={
                    '_time': time.time() - start_time,
                    '_memory': self.resourceWatch.virtual_memory().percent
                }
            )

            # resource check
            self.resourceCheck()

            # legacy writer
            legacy = self.writeLegacy(
                saveLocation=expsMulti.exportLocation,
                expID=self.IDNow,
            )
            legacyTag = tuple(legacy['tags']) if isinstance(
                legacy['tags'], list) else legacy['tags']

            # packing
            expsMulti.tagMapExpsID[legacyTag].append(self.IDNow)
            expsMulti.tagMapFiles[legacyTag].append(legacy['filename'])
            expsMulti.tagMapIndex[legacyTag].append(config['expIndex'])
            
            expsMulti.tagMapQuantity[legacyTag].append(quantity)
            expsMulti.tagMapCounts[legacyTag].append(counts)

        print(f"| Export...")
        expsMulti.gitignore.ignore('*.json')
        expsMulti.state = 'completed'
        
        for k in self._tagMapStateDepending._fields+self._tagMapNeccessary._fields:
            expsMulti.independentExports.append(k)
        dataMultiJobs = expsMulti._jsonize()
        
        for k in self._tagMapStateDepending._fields+self._tagMapNeccessary._fields:
            expsMulti[k].export(
                saveLocation=expsMulti.exportLocation,
                additionName=expsMulti.expsName,
                name=k,
                filetype=expsMulti.filetype
            )
            expsMulti.gitignore.sync(f'*.{k}.{expsMulti.filetype}')
            del dataMultiJobs[k]

        quickJSONExport(
            content=dataMultiJobs,
            filename=expsMulti.exportLocation /
            f"{expsMulti.expsName}.multiJobs.json",
            mode='w+',
            jsonablize=True
        )

        expsMulti.gitignore.export(expsMulti.exportLocation)
        gc.collect()
        print(
            f"| MultiOutput {self.__name__} End in {self._time_takes(start_time)} ...\n" +
            f"+"+"-"*20)

        return expsMulti
