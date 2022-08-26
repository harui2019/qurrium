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
    # IBMQJobManagerInvalidStateError,
    # IBMQJobManagerUnknownJobSet
)

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

from ..mori import (
    defaultConfig,
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
from ..util import Gajima, ResoureWatch

from .runargs import (
    transpileConfig,
    managerRunConfig,
    runConfig,
    ResoureWatchConfig,
    containChecker,
)
from .exceptions import (
    UnconfiguredWarning,
    InvalidConfiguratedWarning,
)
from .type import Quantity, Counts, waveGetter, waveReturn

# Qurry V0.4.0 - a Qiskit Macro


def defaultCircuit(numQubit: int) -> QuantumCircuit:
    return QuantumCircuit(
        numQubit, numQubit, name=f'qurry_default_{numQubit}')


class QurryV4:
    """Qurry V0.4.0
    The qiskit job tool
    """
    __version__ = (0, 4, 0)

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

    _v3ArgsMapping = {
        'runConfig': 'runArgs',
    }

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

    # TODO: make hint available in qurry

    """ Initialize """

    @abstractmethod
    def initialize(self) -> dict[str, any]:
        """defaultConfig to Initialize QurryV4.

        Returns:
            dict[str, any]: The basic defaultConfig of `Qurry`.
        """

    def initialize(self) -> dict[str, any]:

        self._expsBase = defaultConfig(
            name='QurriumMultiBase',
            default={
                **self.argsMain()._asdict(),
                **self.argsCore()._asdict(),
                **self.expsMain()._asdict(),
            },
        )
        self._expsHint = {
            **{k: f"sample: {v}" for k, v in self._expsBase},
            "_basicHint": "This is a hint of QurryV4.",
        }
        self._expsMultiBase = defaultConfig(
            name='QurriumMultiBase',
            default={
                **self.argsMultiMain()._asdict(),
                **self.expsMultiMain()._asdict(),
            },
        )
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
            KeyError: defaultConfig lost.
            KeyError: `self.measureConfig['hint']` is not completed.
        """
        # basic check
        if hasattr(self, 'initialize'):
            self.initialize()
            for k in ['_expsMultiBase', '_expsBase', '_expsHint', 'shortName']:
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
            defaults=list(self.argsMain._field_defaults.values()) +
            list(self.argsCore._field_defaults.values()),
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
    ) -> tuple[argsCore, dict[str, any]]:
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

        return (
            self.argsCore(**{
                'wave': wave,
                'expsName': f"{expsName}.{wave}",
                'sampling': sampling,
            }),
            {
                k: v for k, v in otherArgs.items()
                if k not in self.argsCore._fields
            }
        )

    def paramsControlMain(
        self,
        # ID of experiment.
        expID: Optional[str] = None,
        # Qiskit argument of experiment.
        # Multiple jobs shared
        shots: int = 1024,
        backend: Backend = AerProvider().get_backend('aer_simulator'),
        provider: Optional[AccountProvider] = None,
        runArgs: dict[str, any] = {},
        # Single job dedicated
        runBy: str = "gate",
        decompose: Optional[int] = 2,
        transpileArgs: dict[str, any] = {},
        # Other arguments of experiment
        drawMethod: str = 'text',
        resultKeep: bool = False,
        tags: Optional[Hashable] = None,
        resoureControl: dict[str, any] = {},
        # export option
        expIndex: Optional[int] = None,
        saveLocation: Optional[Union[Path, str]] = None,
        exportLocation: Optional[Path] = None,
        # other
        **otherArgs: any,
    ) -> Union[argsMain, argsCore]:
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
                defaultConfig of :func:`qiskit.execute`.
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
                defaultConfig of :func:`qiskit.transpile`.
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

        # config check
        for config, checker in [
            (runArgs, runConfig),
            (transpileArgs, transpileConfig),
            (resoureControl, ResoureWatchConfig),
        ]:
            containChecker(config, checker)

        self.resourceWatch = ResoureWatch(**resoureControl)

        # Export all arguments
        coreFiltered, otherParams = self.paramsControlCore(**otherArgs)
        coreParams = coreFiltered._asdict()
        if len(otherParams) > 0:
            warnings.warn(
                f"The following keys are not recognized as arguments for main process of experiment: " +
                f"{list(otherParams.keys())}'" +
                ', but are still kept in experiment record.',
                InvalidConfiguratedWarning
            )

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
            'resoureControl': resoureControl,

            'saveLocation': saveLocation,
            'exportLocation': exportLocation,

            'expIndex': expIndex,

            **coreParams
        })
        self.exps[self.IDNow] = {
            **otherParams,
            **self._expsBase.make(),
            **self.now._asdict(),
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
        _clear: bool = False,
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

        if isinstance(saveLocation, (Path, str)):
            saveLocParts = Path(saveLocation).parts
            saveLoc = Path(saveLocParts[0]) if len(
                saveLocParts) > 0 else Path('./')
            for p in saveLocParts[1:]:
                saveLoc /= p
            if not os.path.exists(saveLoc):
                os.mkdir(saveLoc)

            if _isMulti:
                legacysLib = saveLoc / 'legacy'
                if not os.path.exists(legacysLib):
                    os.mkdir(legacysLib)
            else:
                legacysLib = saveLoc

            self.exps[legacyId]['saveLocation'] = legacysLib
            legacyExport = jsonablize(exports)
            with open((legacysLib / (filename+'.json')), 'w+', encoding='utf-8') as Legacy:
                json.dump(
                    legacyExport, Legacy, indent=2, ensure_ascii=False)

            tales = self.exps[legacyId]['sideProduct']
            if len(tales) > 0:
                talesLib = saveLoc / 'tales'
                if not os.path.exists(talesLib):
                    os.mkdir(talesLib)

                for k in tales:
                    talesExport = jsonablize(tales[k])
                    with open((talesLib / (filename+f'.{k}.json')), 'w+', encoding='utf-8') as Tales:
                        json.dump(
                            talesExport, Tales, indent=2, ensure_ascii=False)

        else:
            legacyExport = jsonablize(exports)
            if saveLocation != None:
                warnings.warn(
                    "'saveLocation' is not the type of 'str' or 'Path', " +
                    "so export cancelled.")

        if _clear:
            print("| "+"\u001b[1m"+f"exps={legacyId} clear..."+"\u001b[0m")
            del self.exps[legacyId]
            gc.collect()

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
                lost = self._expsBase.check(
                    legacyRead, ignores=self._expsBaseExceptKeys)
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
    def quantities(cls) -> Union[dict[str, float], expsCore]:
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

        quantity = quantity if isinstance(
            quantity, dict) else quantity._asdict()

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

    class managedReturn(NamedTuple):
        managedJob: ManagedJobSet
        jobID: str
        report: str
        name: str
        type: Literal['pending', 'retrieve']

    def pending(
        self,
        experiments: list,
        backend: Backend,
        shots: int = 1024,
        name: str = 'qurryV4',
        managerRunArgs: dict[str, any] = {},
    ) -> managedReturn:
        """_summary_

        Args:
            experiments (list): _description_
            backend (Backend): _description_
            shots (int, optional): _description_. Defaults to 1024.
            name (str, optional): _description_. Defaults to 'qurryV4'.

        Returns:
            dict[str, str]: _description_
        """

        pendingJob = self.jobManager.run(
            **managerRunArgs,
            experiments=experiments,
            backend=backend,
            shots=shots,
            name=name,
        )
        jobID = pendingJob.job_set_id()
        report = pendingJob.report()
        name = pendingJob.name()

        return self.managedReturn(
            managedJob=pendingJob,
            jobID=jobID,
            report=report,
            name=name,
            type='pending'
        )

    def retrieve(
        self,
        jobID: str,
        provider: AccountProvider,
        refresh: bool = False,
    ) -> managedReturn:
        """_summary_

        Args:
            jobID (str): _description_
            provider (AccountProvider): _description_
            refresh (bool, optional): _description_. Defaults to False.

        Returns:
            ManagedResults: _description_
        """

        retrievedJob = self.jobManager.retrieve_job_set(
            job_set_id=jobID,
            provider=provider,
            refresh=refresh,
        )
        jobID = retrievedJob.job_set_id()
        report = retrievedJob.report()
        name = retrievedJob.name()

        return self.managedReturn(
            managedJob=retrievedJob,
            jobID=jobID,
            report=report,
            name=name,
            type='retrieve'
        )

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

    def _multiDataGenOrRead(
        self,
        namingComplex: _namingComplex,
        initedConfigList: list,

        state: Literal["init", "pending", "completed"],
        isRead: bool = False,
        isRetrieve: bool = False,
        overwrite: bool = False,
    ) -> tuple[dict[str, any], argsMultiMain, Union[
        expsMultiMain,
        _tagMapNeccessary,
        _tagMapStateDepending,
        _tagMapUnexported,
        attributedDict
    ]]:
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
                circuitsMap: TagMapType[str] = TagMap()

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

        version = 4
        if isRead:
            dataDummyJobs: dict[any] = {}
            dataPowerJobsName = namingComplex.exportLocation / \
                f"{namingComplex.expsName}.powerJobs.json"
            dataMultiJobsName = namingComplex.exportLocation / \
                f"{namingComplex.expsName}.multiJobs.json"

            if not os.path.exists(namingComplex.exportLocation / "legacy"):
                version = 3

            # read
            if os.path.exists(dataPowerJobsName):
                with open(dataPowerJobsName, 'r', encoding='utf-8') as theData:
                    dataDummyJobs = json.load(theData)
                jobsType = "powerJobs"

            else:
                with open(dataMultiJobsName, 'r', encoding='utf-8') as theData:
                    dataDummyJobs = json.load(theData)
                jobsType = "multiJobs"
            dataDummyJobs['jobsType'] = jobsType

            # key check
            lostKey = []
            for k in (self._powerJobKeyRequired if jobsType == "powerJobs" else self._multiJobKeyRequired):
                if k not in dataDummyJobs:
                    lostKey.append(k)
            if len(lostKey) > 0:
                raise ValueError(
                    f"'{lostKey}' are the key required in 'powerJob', otherwise this file may be broken.")

            # handle v3 key name and value redefined
            for k in list(dataDummyJobs):
                if k in self._v3MultiArgsMapping:
                    dataDummyJobs[self._v3MultiArgsMapping[k]
                                  ] = dataDummyJobs[k]
            if "independentExports" in dataDummyJobs:
                if isinstance(dataDummyJobs["independentExports"], bool):
                    dataDummyJobs["independentExports"] = self._independentExportDefault

            # Data Read
            # state check
            if 'state' in dataDummyJobs:
                state = dataDummyJobs['state']
            else:
                warnings.warn(f"'state' no found, use '{state}'.")

            rawPowerJobID = []
            if 'powerJobID' in dataDummyJobs:
                rawPowerJobID = dataDummyJobs['powerJobID']
            # powerJobID and handle v3
            if isinstance(rawPowerJobID, str):
                rawPowerJobID = [[rawPowerJobID, "power"]]
            elif rawPowerJobID is None:
                rawPowerJobID = []
            elif isinstance(rawPowerJobID, list):
                ...
            else:
                raise TypeError(
                    f"Invalid type '{type(rawPowerJobID)}' for 'powerJobID', only 'str', 'list[tuple[str, list]]', or 'None' are available.")
            powerJobID = []
            for pendingID, pendingTag in rawPowerJobID:
                if isinstance(pendingTag, list):
                    pendingTag = tuple(pendingTag)
                powerJobID.append((pendingID, pendingTag))

            # tagMapStateDepending
            if state == 'completed' and not overwrite:
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
                tagMapStateDepending = self._tagMapStateDepending(**{
                    k: TagMap({}, k)
                    for k in self._tagMapStateDepending._fields})

            # tagMapUnexported
            tagMapUnexported = self._tagMapUnexported(**{
                k: TagMap({}, k)
                for k in self._tagMapUnexported._fields})
            # tagMapNeccessary
            if version == 3:
                tagMapNeccessary = self._tagMapNeccessary(
                    tagMapExpsID=dataDummyJobs['tagMapExpsID'],
                    tagMapFiles=TagMap({
                        'power': dataDummyJobs['listFile']
                    }),
                    tagMapIndex=TagMap(dataDummyJobs['tagMapIndex']),
                    circuitsMap=TagMap(dataDummyJobs['circuitsMap']),
                    pendingPools=TagMap({
                        'power': [i for i in range(sum(dataDummyJobs['circuitsNum'].values()))]
                    })
                )

            else:
                tagMapNeccessary = self._tagMapNeccessary(**{
                    k: TagMap(dataDummyJobs[k]) if k in dataDummyJobs else TagMap.read(
                        saveLocation=namingComplex.exportLocation,
                        tagmapName=k,
                    )
                    for k in self._tagMapNeccessary._fields})

            circuitsNum: dict[str, int] = dataDummyJobs['circuitsNum']
            gitignore: syncControl = (syncControl(
                dataDummyJobs['gitignore']) if 'gitignore' in dataDummyJobs else syncControl())

            configDict = {}
            if os.path.exists(namingComplex.exportLocation /
                              f"{namingComplex.expsName}.configDict.json"):
                with open((
                        namingComplex.exportLocation / f"{namingComplex.expsName}.configDict.json"),
                        'r', encoding='utf-8') as theData:
                    configDict = json.load(theData)
            if 'configList' in dataDummyJobs:
                for config in dataDummyJobs['configDict']:
                    configDict[dataDummyJobs['listFile']
                               [config['expIndex']]] = config

        else:
            # Data Gen
            # tagMapStateDepending
            tagMapStateDepending = self._tagMapStateDepending(**{
                k: TagMap({}, k)
                for k in self._tagMapStateDepending._fields})
            # tagMapUnexported
            tagMapUnexported = self._tagMapUnexported(**{
                k: TagMap({}, k)
                for k in self._tagMapUnexported._fields})
            # tagMapUnexported
            tagMapNeccessary = self._tagMapNeccessary(**{
                k: TagMap({}, k)
                for k in self._tagMapNeccessary._fields})

            circuitsNum: dict[str, int] = {}
            powerJobID: dict[str, int] = []
            gitignore: syncControl = syncControl()

            configDict = {}

            dataDummyJobs = {}

        # reading experiment datas
        if isRead:
            for tags, files in tagMapNeccessary.tagMapExpsID.items():
                for expIDKey in files:
                    self.exps[expIDKey] = self.readLegacy(
                        expID=expIDKey,
                        saveLocation=Path(namingComplex.exportLocation),
                        _isMulti=True,
                    )

        tmpExpMultiPartial = self.expsMultiMain(**{
            'configList': initedConfigList,
            'configDict': configDict,

            'powerJobID': powerJobID,
            'gitignore': gitignore,

            'circuitsNum': circuitsNum,
            'state': state,
        })

        tmpExpMulti = attributedDict(
            params={
                **tmpExpMultiPartial._asdict(),
                # tagMapStateDepending
                **tagMapStateDepending._asdict(),
                # tagMapUnexported
                **tagMapUnexported._asdict(),
                # tagMapNeccessary
                **tagMapNeccessary._asdict(),
            }
        )

        tmpArgsMulti = {}
        for k in list(dataDummyJobs.keys()):
            if k in self.expsMultiMain._fields:
                del dataDummyJobs[k]
            elif k in self._tagMapStateDepending._fields:
                del dataDummyJobs[k]
            elif k in self._tagMapUnexported._fields:
                del dataDummyJobs[k]
            elif k in self._tagMapNeccessary._fields:
                del dataDummyJobs[k]
            elif k in self.argsMultiMain._fields:
                tmpArgsMulti[k] = dataDummyJobs[k]
                del dataDummyJobs[k]

        tmpArgsMulti = self.argsMultiMain(**tmpArgsMulti)

        return dataDummyJobs, tmpArgsMulti, tmpExpMulti

    def paramsControlMulti(
        self,
        # configList
        configList: list = [],

        # defaultConfig of `IBMQJobManager().run`
        # Multiple jobs shared
        shots: int = 1024,
        backend: Backend = AerProvider().get_backend('aer_simulator'),
        provider: AccountProvider = None,
        # IBMQJobManager() dedicated
        managerRunArgs: dict[str, any] = {
            'max_experiments_per_job': 200,
        },
        # Other arguments of experiment
        # Multiple jobs shared
        expsName: str = 'exps',
        saveLocation: Union[Path, str] = Path('./'),

        pendingStrategy: Literal['power', 'tags', 'onetime'] = 'power',
        jobsType: Literal["multiJobs", "powerJobs"] = "multiJobs",
        isRetrieve: bool = False,
        isRead: bool = False,
        clear: bool = False,
        # independentExports: list[str] = _independentExportDefault,
        filetype: TagMap._availableFileType = 'json',

        # powerJobID: Optional[Union[str, list[str]]] = None,
        state: Literal["init", "pending", "completed"] = "init",
        overwrite: bool = False,

        **otherArgs: any,
    ) -> Union[
        argsMultiMain,
        expsMultiMain,
        _tagMapNeccessary,
        _tagMapStateDepending,
        _tagMapUnexported
    ]:
        """Handling all arguments and initializing a single experiment.

        - example of a value in `self.exps`

        ```
        {
            # configList
            'configList': [],

            # defaultConfig of `IBMQJobManager().run`
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
                The list of defaultConfig of multiple experiment.

            # defaultConfig of `IBMQJobManager().run`
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
                defaultConfig of :func:`IBMQJobManager().run`.
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
        if 'name' in otherArgs:
            expsName = otherArgs['name']
        namingComplex = self._multiNaming(
            isRead=isRead,
            expsName=expsName,
            saveLocation=saveLocation,
        )

        if provider is None and hasattr(backend, 'provider'):
            provider = backend.provider()

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
        dataDummyJobs, readArgs, dataGenerator = self._multiDataGenOrRead(
            initedConfigList=initedConfigList,
            namingComplex=namingComplex,

            state=state,
            isRead=isRead,
            isRetrieve=isRetrieve,
            overwrite=overwrite,
        )

        if len(dataDummyJobs) > 0:
            print("| The following are useless value:", dataDummyJobs)

        # config check
        for config, checker in [
            (managerRunArgs, managerRunConfig),
        ]:
            containChecker(config, checker)

        # independentExports check
        independentExports: list[str] = self._independentExportDefault
        # for e in self._independentExportDefault:
        #     if e not in independentExports:
        #         independentExports.append(e)

        self.multiNow: QurryV4.argsMultiMain = self.argsMultiMain(**{
            # defaultConfig of `IBMQJobManager().run`
            # Multiple jobs shared
            'shots': readArgs.shots if isRead else shots,
            'backend': backend,
            'provider': provider,

            # IBMQJobManager() dedicated
            'managerRunArgs': readArgs.managerRunArgs if isRead else managerRunArgs,

            # Other arguments of experiment
            # Multiple jobs shared
            'expsName': namingComplex.expsName,
            'saveLocation': namingComplex.saveLocation,
            'exportLocation': namingComplex.exportLocation,

            'pendingStrategy': readArgs.pendingStrategy if isRead else pendingStrategy,
            'jobsType': readArgs.jobsType if isRead else jobsType,

            'isRetrieve': isRetrieve,
            'isRead': isRead,
            'clear': readArgs.clear if isRead else clear,
            'independentExports': readArgs.independentExports if isRead else independentExports,
            'filetype': filetype,
        })

        self.expsMulti: Union[
            QurryV4.argsMultiMain,
            QurryV4.expsMultiMain,
            QurryV4._tagMapNeccessary,
            QurryV4._tagMapStateDepending,
            QurryV4._tagMapUnexported,
            attributedDict
        ] = attributedDict(
            params={
                **otherArgs,
                **self.multiNow._asdict(),
                **dataGenerator._asdict(),
                **dataDummyJobs,
            }
        )

        return self.expsMulti

    @classmethod
    def _multiExport(
        cls,
        expsMulti: Union[argsMultiMain, expsMultiMain],
    ) -> None:
        """Data export.

        Args:
            expsMulti (Union[argsMultiMain, expsMultiMain]): expsMulti.
        """
        print(f"| Export...")
        for k in (
            cls._tagMapStateDepending._fields +
            cls._tagMapNeccessary._fields
        ):
            if k not in expsMulti.independentExports:
                expsMulti.independentExports.append(k)

        expsMulti.gitignore.ignore('*.json')
        expsMulti.gitignore.sync(f"*.{expsMulti.jobsType}.json")

        dataMultiJobs = expsMulti._jsonize()

        for k in expsMulti.independentExports:
            if k in cls._tagMapStateDepending._fields:
                if expsMulti.state == 'pending':
                    del dataMultiJobs[k]

            if hasattr(expsMulti[k], 'export'):
                expsMulti[k].export(
                    saveLocation=expsMulti.exportLocation,
                    additionName=expsMulti.expsName,
                    name=k,
                    filetype=expsMulti.filetype
                )
                expsMulti.gitignore.sync(f'*.{k}.{expsMulti.filetype}')
                if k in dataMultiJobs:
                    del dataMultiJobs[k]

            elif isinstance(expsMulti[k], (dict, list)):
                quickJSONExport(
                    content=dataMultiJobs[k],
                    filename=expsMulti.exportLocation /
                    f"{expsMulti.expsName}.{k}.json",
                    mode='w+',
                    jsonablize=True
                )
                del dataMultiJobs[k]

            else:
                warnings.warn(
                    f"'{k}' is type '{type(expsMulti[k])}' which is not supported to export.")

        for k in cls._unexport:
            del dataMultiJobs[k]

        quickJSONExport(
            content=dataMultiJobs,
            filename=expsMulti.exportLocation /
            f"{expsMulti.expsName}.{expsMulti.jobsType}.json",
            mode='w+',
            jsonablize=True
        )

        expsMulti.gitignore.export(expsMulti.exportLocation)

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

        # defaultConfig of `IBMQJobManager().run`
        # Multiple jobs shared
        shots: int = 1024,
        backend: Backend = AerProvider().get_backend('aer_simulator'),

        # Multiple jobs shared
        expsName: str = 'exps',
        saveLocation: Union[Path, str] = Path('./'),
        clear: bool = False,

        **allArgs: any,
    ) -> dict[any]:
        """Make multiple jobs output.

        Args:        
            configList (list):
                The list of defaultConfig of multiple experiment.

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
            # defaultConfig of `IBMQJobManager().run`
            # Multiple jobs shared
            shots=shots,
            backend=backend,
            # Other arguments of experiment
            # Multiple jobs shared
            expsName=expsName,
            saveLocation=saveLocation,

            jobsType='powerJobs',
            isRetrieve=False,
            isRead=False,
            clear=clear,
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
                _isMulti=True,
            )
            legacyTag = tuple(legacy['tags']) if isinstance(
                legacy['tags'], list) else legacy['tags']

            # packing
            expsMulti.tagMapExpsID[legacyTag].append(self.IDNow)
            expsMulti.tagMapFiles[legacyTag].append(legacy['filename'])
            expsMulti.tagMapIndex[legacyTag].append(config['expIndex'])

            numCirc = len(self.exps[self.IDNow]['circuit'])
            expsMulti.circuitsNum[self.IDNow] = numCirc
            expsMulti.configDict[self.IDNow] = config
            
            expsMulti.circuitsMap[self.IDNow].append(
                [c for c in range(numCirc)])

            expsMulti.tagMapQuantity[legacyTag].append(quantity)
            expsMulti.tagMapCounts[legacyTag].append(counts)

        # Export
        expsMulti.state = 'completed'

        self._multiExport(expsMulti)

        gc.collect()
        print(
            f"| MultiOutput {self.__name__} End in {self._time_takes(start_time)} ...\n" +
            f"+"+"-"*20)

        return expsMulti

    def multiPending(
        self,
        # configList
        configList: list = [],

        # defaultConfig of `IBMQJobManager().run`
        # Multiple jobs shared
        shots: int = 1024,
        backend: Backend = AerProvider().get_backend('aer_simulator'),

        # Multiple jobs shared
        expsName: str = 'exps',
        saveLocation: Union[Path, str] = Path('./'),

        pendingStrategy: Literal['power', 'tag', 'each'] = 'power',
        _clear: bool = False,

        **allArgs: any,
    ) -> dict[any]:
        """Make multiple jobs output.

        Args:        
            configList (list):
                The list of defaultConfig of multiple experiment.

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
            # defaultConfig of `IBMQJobManager().run`
            # Multiple jobs shared
            shots=shots,
            backend=backend,
            # Other arguments of experiment
            # Multiple jobs shared
            expsName=expsName,
            saveLocation=saveLocation,

            pendingStrategy=pendingStrategy,
            jobsType='powerJobs',
            isRetrieve=False,
            isRead=False,
            clear=_clear,
            **allArgs
        )

        allTranspliedCircs = {}
        pendingArray = []

        print(f"| MultiPending {self.__name__} Start...\n"+f"+"+"-"*20)
        numConfig = len(expsMulti.configList)
        for config in expsMulti.configList:
            print(
                f"| index={config['expIndex']}/{numConfig} - {self._time_takes(start_time)}.")
            circuitSet = self.transpiler(**config)
            allTranspliedCircs[self.IDNow] = circuitSet

            # resource check
            self.resourceCheck()

            # legacy writer
            legacy = self.writeLegacy(
                saveLocation=expsMulti.exportLocation,
                expID=self.IDNow,
                _isMulti=True,
                _clear=expsMulti.clear,
            )
            legacyTag = tuple(legacy['tags']) if isinstance(
                legacy['tags'], list) else legacy['tags']

            # packing
            expsMulti.tagMapExpsID[legacyTag].append(self.IDNow)
            expsMulti.tagMapFiles[legacyTag].append(legacy['filename'])
            expsMulti.tagMapIndex[legacyTag].append(config['expIndex'])

            numCirc = len(circuitSet)
            expsMulti.circuitsNum[self.IDNow] = numCirc
            expsMulti.configDict[self.IDNow] = config

        expIDList = expsMulti.tagMapExpsID.all()

        with Gajima(
            enumerate(expIDList),
            carousel=[('dots', 20, 6), 'basic'],
            prefix="| ",
            desc="Packing circuits for pending",
            finish_desc="Packing Completed",
        ) as gajima:

            for expIndex, expIDKey in gajima:
                tmpCircNum = expsMulti.circuitsNum[expIDKey]
                gajima.gprint(
                    f"| Packing expID: {expIDKey}, index={expIndex} with {tmpCircNum} circuits ...")

                for i in range(tmpCircNum):
                    expsMulti.circuitsMap[expIDKey].append(len(pendingArray))

                    if pendingStrategy == 'each':
                        expsMulti.pendingPools[f"exp={expIDKey}"].append(
                            len(pendingArray))

                    elif pendingStrategy == 'tags':
                        tags = self.exps[expIDKey]['tags']
                        expsMulti.pendingPools[tags].append(len(pendingArray))

                    else:
                        if pendingStrategy != 'power':
                            warnings.warn(
                                f"Unknown strategy '{pendingStrategy}, use 'power'.")
                        expsMulti.pendingPools['power'].append(
                            len(pendingArray))

                    pendingArray.append(allTranspliedCircs[expIDKey][i])

        print("| "+"\u001b[1m"+"Pending Strategy: " +
              pendingStrategy + "\u001b[0m")

        with Gajima(
            carousel=[('dots', 20, 6), 'basic'],
            prefix="| ",
            desc="Pending Jobs",
            finish_desc="Pending finished and Exporting",
        ) as gajima:

            expsMulti.powerJobID = []
            for pk, pcircs in expsMulti.pendingPools.items():
                if len(pcircs) > 0:
                    pJobs = self.pending(
                        experiments=[pendingArray[ci] for ci in pcircs],
                        backend=expsMulti.backend,
                        shots=expsMulti.shots,
                        name=f'{expsMulti.expsName}-{pk}_w/{len(pcircs)}_jobs',
                        managerRunArgs=expsMulti.managerRunArgs,
                    )
                    expsMulti.powerJobID.append((pJobs.jobID, pk))
                    gajima.gprint(f"| report:", pJobs.report)
                    gajima.gprint(f"| name: {pJobs.name}")

                else:
                    if not pk == 'noTags':
                        warnings.warn('There is no circuits in', pk)

        # Export
        expsMulti.state = 'pending'
        expsMulti.jobsType = 'powerJobs'
        for k in self._tagMapNeccessary._fields:
            if k not in expsMulti.independentExports:
                expsMulti.independentExports.append(k)

        self._multiExport(expsMulti)

        gc.collect()
        print(
            f"| MultiPending {self.__name__} End in {self._time_takes(start_time)} ...\n" +
            f"+"+"-"*20)

        return expsMulti

    def multiRetrieve(
        self,
        exportName: Union[Path, str],
        saveLocation: Union[Path, str] = './',
        provider: AccountProvider = None,
        overwrite: bool = False,
        refresh: bool = False,
        **allArgs: any,
    ) -> dict[any]:
        """_summary_

        Args:
            exportName (Union[Path, str]): _description_
            saveLocation (Union[Path, str], optional): _description_. Defaults to './'.
            overwrite (bool, optional): _description_. Defaults to False.

        Returns:
            dict[any]: _description_
        """
        start_time = time.time()
        expsMulti = self.paramsControlMulti(
            saveLocation=saveLocation,
            expsName=exportName,
            provider=provider,
            isRead=True,
            isRetrieve=True,
            overwrite=overwrite,
            **allArgs,
        )

        print(f"| MultiRetrieve {self.__name__} Start...\n"+f"+"+"-"*20)
        if expsMulti.jobsType == 'multiJobs':
            print(
                f"| MultiRetrieve {self.__name__} End " +
                f"with reading a multiJobs in {time.time() - start_time} sec ...\n" +
                f"+"+"-"*20)
            return expsMulti

        pendingMapping: dict[Union[str, tuple[str]],
                             QurryV4.managedReturn] = {}
        allCircuitCountsDict: dict[int, Counts] = {}
        expIDBaseCountsMapping = TagMap()

        if expsMulti.state == 'pending':
            print(f"| Retrieve result...")
            for pendingID, pk in expsMulti.powerJobID:
                print(f"| retrieve: {pendingID} {pk}")
                pendingMapping[pk] = self.retrieve(
                    jobID=pendingID,
                    provider=expsMulti.provider,
                    refresh=refresh,
                )

        elif overwrite and isinstance(overwrite, bool):
            print(f"| Overwrite activate and retrieve result...")
            for pendingID, pk in expsMulti.powerJobID:
                pendingMapping[pk] = self.retrieve(
                    jobID=pendingID,
                    provider=expsMulti.provider,
                    refresh=refresh,
                )

        else:
            print(
                f"| MultiRetrieve {self.__name__} End " +
                f"with loading completed powerJobs in {time.time() - start_time} sec ...\n" +
                f"+"+"-"*20)
            return expsMulti

        print(
            f"| Retrieved all result to distribute - {time.time() - start_time} sec ...")

        with Gajima(
            carousel=[('dots', 20, 6), 'basic'],
            prefix="| ",
            desc="Distributing all result",
            finish_desc="Distributed all result to computing",
        ) as gajima:

            gajima.gprint("| Listing all circuits")
            for pk, pcircs in expsMulti.pendingPools.items():
                if pk == 'all':
                    ...
                elif len(pcircs) > 0:
                    pJob: ManagedJobSet = pendingMapping[pk].managedJob
                    pResult = pJob.results()
                    counts = self.counts(
                        result=pResult,
                        resultIdxList=[rk-pcircs[0] for rk in pcircs]
                    )
                    for rk in pcircs:
                        allCircuitCountsDict[rk] = counts[rk-pcircs[0]]

                else:
                    if not pk == 'noTags':
                        warnings.warn('There is no circuits in', pk)

            gajima.gprint(
                "| Distributing all circuits to their original experimemts.")
            for expID, circIndexList in expsMulti.circuitsMap.items():
                for circIndex in circIndexList:
                    expIDBaseCountsMapping[expID].append(
                        allCircuitCountsDict[circIndex])

        AllExpNum = sum(len(explist)
                        for explist in expsMulti.tagMapExpsID.values())
        with Gajima(
            range(AllExpNum),
            carousel=[('dots', 20, 6), 'basic'],
            prefix="| ",
            desc="Computing all experiment",
            finish_desc="Computing completed and export",
        ) as gajima:

            for tags, expIDList in expsMulti.tagMapExpsID.items():
                for expID in expIDList:
                    self.exps[expID]['counts'] = expIDBaseCountsMapping[expID]
                    expsMulti.tagMapCounts[tags].append(counts)

                    quantitiesWSideProduct = self.quantities(
                        **self.exps[expID],
                        # counts=counts,
                    )
                    for k in quantitiesWSideProduct:
                        if k[0] == '_' and k != '_dummy':
                            self.exps[expID]['sideProduct'][k[1:]
                                                            ] = quantitiesWSideProduct[k]
                    quantity = {k: quantitiesWSideProduct[k]
                                for k in quantitiesWSideProduct if k[0] != '_'}
                    self.exps[expID] = {
                        **self.exps[expID],
                        **quantity,
                        'counts': counts,
                    }

                    # TODO: update gajima
                    try:
                        next(gajima)
                    except StopIteration:
                        gajima.gprint('Iteration number may wrong.')

                    expsMulti.tagMapQuantity[tags].append(quantity)

        expsMulti.state = 'completed'
        self._multiExport(expsMulti)

        gc.collect()
        print(
            f"| MultiRetrieve {self.__name__} End in {self._time_takes(start_time)} ...\n" +
            f"+"+"-"*20)

        return expsMulti

    """Other"""

    def reset(
        self,
        *args,
        security: bool = False,
    ) -> None:
        """Reset the measurement and release memory.

        Args:
            security (bool, optional): Security for reset. Defaults to `False`.
        """

        if security and isinstance(security, bool):
            self.__init__(self.waves)
            gc.collect()
            warnings.warn(
                "The measurement has reset and release memory allocating.")
        else:
            warnings.warn(
                "Reset does not execute to prevent executing accidentally, " +
                "if you are sure to do this, then use '.reset(security=True)'."
            )

    def __repr__(self) -> str:
        return f"<{self.__name__}({len(self.exps)} experiments made)>"
