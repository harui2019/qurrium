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
    # ManagedJobSet,
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
from collections import Counter

from ..util import Gajima, ResoureWatch
from ..mori import (
    Configuration,
    attributedDict,
    syncControl,
    jsonablize,
    quickJSONExport,
    keyTupleLoads,
    sortHashableAhead,
    TagMap,
    singleColCSV,
)
from ..mori.type import TagMapType
from .exceptions import UnconfiguredWarning
from .type import (
    Quantity,
    Counts,
    waveGetter,
    waveReturn,
)

# Qurry V0.3.2 - a Qiskit Macro


def defaultCircuit(numQubit: int) -> QuantumCircuit:
    return QuantumCircuit(
        numQubit, numQubit, name=f'qurry_default_{numQubit}')


class QurryV3:
    """Qurry V0.3.1
    The qiskit job tool
    """

    """ Configuration """
    
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
        runConfig: dict = {}

        # Single job dedicated
        runBy: str = "gate"
        decompose: Optional[int] = 2
        transpileArgs: dict = {}

        # Other arguments of experiment
        drawMethod: str = 'text'
        resultKeep: bool = False
        dataRetrieve: Optional[dict[Union[list[str], str]]] = None
        expsName: str = 'exps'
        tags: Optional[Hashable] = None

    def expsConfig(
        self,
        name: str = 'qurryConfig',
        defaultArg: dict[any] = {
            **argsCore()._asdict()
        },
    ) -> Configuration:
        """The default format and value for executing a single experiment.
        - Example:

        ```python
        _expsConfig = expsConfig(
            name='dummyConfig',
            defaultArg={
                'wave': None,
                'dummy': None,
            },
        )
        ```
        Then `_expsConfig` will be
        ```python
        {
            # ID of experiment.
            'expID': None,

            # Variants of experiment.
            **defaultArg,

            # Qiskit argument of experiment.
            # Multiple jobs shared
            'shots': 1024,
            'backend': AerProvider().get_backend('aer_simulator'),
            'runConfig': {}

            # Single job dedicated
            'runBy': "gate",
            'decompose': 1,
            'transpileArgs': {},

            # Other arguments of experiment
            'drawMethod': 'text',
            'resultKeep': False,
            'dataRetrieve': None,
        }
        ```

        Args:
            name (str, optional):
                Name of basic configuration for `Qurry`.
                Defaults to 'qurryConfig'.
            defaultArg (dict[any], optional):
                Basic input for `.output`.
                Defaults to { 'wave': None }.

        Returns:
            Configuration: The template of experiment configuration.
        """
        return Configuration(
            name=name,
            default={
                **self.argsMain()._asdict(),
                # Variants of experiment.
                **defaultArg,
            },
        )

    def expsBase(
        self,
        name: str = 'qurryExpsBase',
        defaultArg: dict = {
            # Result of experiment.
        },
    ) -> Configuration:
        """The default storage format and values of a single experiment.
        - Example:

        ```python
        _expsBase = expsBase(
            name='dummyBase',
            expsConfig= _expsConfig,
            defaultArg={
                'dummyResult1': None,
                'dummyResult2': None,
            },
        )
        ```
        Then `_expsBase` will be
        ```python
        {
            # ID of experiment.
            'expID': None,

            # Variants of experiment.
            **defaultArg,

            # Qiskit argument of experiment.
            # Multiple jobs shared
            'shots': 1024,
            'backend': AerProvider().get_backend('aer_simulator'),
            'provider': 'None',
            'runConfig': {},

            # Single job dedicated
            'runBy': "gate",
            'decompose': 1,
            'transpileArgs': {},

            # Other arguments of experiment
            # Multiple jobs shared
            'expsName': 'exps',

            # Single job dedicated
            'drawMethod': 'text',
            'resultKeep': False,
            'dataRetrieve': None,
            'tag': tag,

            # Reault of experiment.
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
            name (str, optional):
                Name of basic configuration for `Qurry`.
                Defaults to 'qurryConfig'.
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
                # inherit from `expsConfig`
                **self.expsConfig(),

                # Reault of experiment.
                **defaultArg,

                # Measurement result
                'circuit': None,
                'figRaw': 'unexport',
                'figTranspile': 'unexport',
                'result': None,
                'counts': None,

                # Export data
                'jobID': '',
                'expsName': 'exps',

                # side product
                'sideProduct': {},
            },
        )

    def expsBaseExcepts(
        self,
        excepts: list[str] = ['sideProduct', 'tagMapResult'],
    ) -> dict:
        """_summary_

        Args:
            excepts (list[str], optional):
                Key of value wanted to be excluded.
                Defaults to ['sideProduct'].

        Returns:
            dict: The value will be excluded.
        """
        return self.expsBase().make(partial=excepts)

    class argsMultiMain(NamedTuple):
        # configList
        configList: list = []

        # Configuration of `IBMQJobManager().run`
        # Multiple jobs shared
        shots: int = 1024
        backend: Backend = AerProvider().get_backend('aer_simulator')
        provider: AccountProvider = None
        runConfig: dict = {}

        # IBMQJobManager() dedicated
        managerRunArgs: dict = {
            'max_experiments_per_job': 200,
        }

        # Other arguments of experiment
        # Multiple jobs shared
        isRetrieve: bool = False
        expsName: str = 'exps'
        pendingTags: list[str] = []
        independentExports: bool = False

        # `writeLegacy`
        additionName: Optional[str] = None
        saveLocation: Union[Path, str] = Path('./')
        exportLocation: Path = Path('./')

        gitignore: syncControl = syncControl()
        logTime: singleColCSV = singleColCSV()
        logRAM: singleColCSV = singleColCSV()
        listExpID: list = []
        listFile: list = []

        tagMapExpsID: TagMapType[str] = TagMap()
        tagMapIndex: TagMapType[Union[str, int]] = TagMap()
        tagMapQuantity: TagMapType[Quantity] = TagMap()
        tagMapCounts: TagMapType[Counts] = TagMap()
        # tagMapResult: TagMapType[Result] = TagMap()

        circuitsMap: dict = {}
        circuitsNum: dict = {}

        jobsType: str = "multiJobs"
        state: str = "init"

    def expsConfigMulti(
        self,
        name: str = 'qurryConfigMulti',
        defaultArg: dict[any] = {
            # Variants of experiment.
        },
    ) -> Configuration:
        """The default format and value for executing mutiple experiments.
        - Example:

        ```python
        _expsMultiConfig = expsConfigMulti(
            name='dummyConfigMulti',
            expsConfig= _expsConfig,
            defaultArg={
                'dummyMultiVariaint1': None,
                'dummyMultiVariaint2': None,
            },
        )
        ```
        Then `_expsMultiConfig` will be
        ```python
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
            'additionName': 'export',
            'saveLocation': None,
            'exportLocation': None,
        }
        ```

        Args:
            expsName (str, optional):
                Name of basic configuration for `Qurry`.
                Defaults to 'qurryConfig'.
            expsConfig (dict, optional):
                `expsConfig`.
                Defaults to {}.
            defaultArg (dict, optional):
                Basic input for `.output`.
                Defaults to {}.

        Returns:
            Configuration: The template of multiple experiment configuration.
        """

        return Configuration(
            name=name,
            default={
                **self.argsMultiMain()._asdict(),
            },
        )

    # TODO: make hint available in qurry

    def expsHint(
        self,
        name: str = 'qurryBaseHint',
        hintContext: dict = {
            "_basicHint": "This is a hint of QurryV3.",
        },
    ) -> dict:
        """Make hints for every values in :func:`.expsBase()`.
        - Example:

        ```python
        expsHint(
            name: str = 'qurryBaseHint',
            hintContext = {
                'expID': 'This is a expID'. # hint for `expsBase` value
                'dummyResult1': 'This is dummyResult1.', # extra hint
                'dummyResult2': 'This is dummyResult2.', # extra hint
            },
        )
        ```
        Then call `.expHint` will be
        ```python
        {

            'expID': 'This is a expID',
            'shots': '', # value without hint
            ..., # other in `expsBase`

            'dummyResult1': 'This is dummyResult1.', # extra hint
            'dummyResult2': 'This is dummyResult2.', # extra hint

        }
        ```

        Args:
            name (str, optional):
                Name of basic configuration for `Qurry`.
                Defaults to 'qurryBaseHint'.
            hintContext (dict, optional):
                Hints for `.expBase`.
                Defaults to `{
                    "_basicHint": "This is a hint of QurryV3.",
                }`.

        Returns:
            dict: The hints of the experiment data.
        """

        hintDefaults = {k: "" for k in self.expsConfig()}
        hintDefaults = {**hintDefaults, **hintContext}
        return hintDefaults

    """ Initialize """
    
    @abstractmethod
    def initialize(self) -> dict[str, any]:
        """Configuration to Initialize QurryV3.

        Returns:
            dict[str, any]: The basic configuration of `Qurry`.
        """

    def initialize(self) -> dict[str, any]:

        self._expsConfig = self.expsConfig()
        self._expsBase = self.expsBase()
        self._expsHint = self.expsHint()
        self._expsMultiConfig = self.expsConfigMulti()
        self.shortName = 'qurry'
        self.__name__ = 'Qurry'

        return self._expsConfig, self._expsBase,

    def __init__(
        self,
        waves: Union[QuantumCircuit, list[QuantumCircuit]] = defaultCircuit(1),
    ) -> None:
        """The initialization of QurryV3.

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
            for k in ['_expsConfig', '_expsBase', '_expsHint', 'shortName']:
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
        
        # TODO: add params control
        self.resourceWatch = ResoureWatch()

        # reresh per execution.
        self.now = attributedDict(
            params=self._expsConfig.make(),
        )
        self.IDNow = None
        self.multiNow = attributedDict(
            params=self._expsMultiConfig.make(),
        )

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

    def waveInstruction(
        self,
        wave: Union[list[Hashable], Hashable, None] = None,
        runBy: Optional[Literal['gate', 'operator', 'instruction', 'copy']] = None,
        backend: Optional[Backend] = AerProvider().get_backend('aer_simulator'),
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
            return [self.waveInstruction(w, runBy, backend) for w in wave]

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
        return self.waveInstruction(
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
        return self.waveInstruction(
            wave=wave,
            runBy='gate',
        )

    def find(
        self,
        expID: Optional[str] = None,
    ) -> str:
        """Check whether given `expID` is available,
        If does, then return it, otherwise return `False`.
        Or given current `expID` when doesn't give any id.

        Args:
            expID (Optional[str], optional): The `expID` wants to check. Defaults to None.

        Returns:
            str: The available `expID`.
        """

        if expID != None:
            tgtId = expID if expID in self.exps else False
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
        runConfig: dict = {},
        # Single job dedicated
        runBy: str = "gate",
        decompose: Optional[int] = 2,
        transpileArgs: dict = {},
        # Other arguments of experiment
        drawMethod: str = 'text',
        resultKeep: bool = False,
        dataRetrieve: Optional[dict[Union[list[str], str]]] = None,
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
            'runConfig': {},
            'expsName': 'exps',

            # Single job dedicated
            'runBy': "gate",
            'decompose': 1,
            'transpileArgs': {},

            # Other arguments of experiment
            'drawMethod': 'text',
            'resultKeep': False,
            'dataRetrieve': None,
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

            runConfig (dict, optional):
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

            dataRetrieve (Optional[dict[Union[list[str], str]]], optional):
                Data to collect results from IBMQ via `IBMQJobManager`.
                Defaults to `None`.

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
        if expID == None:
            self.IDNow = str(uuid4())
        elif expID == '_dummy':
            print('dummy test.')
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

        # Export all arguments
        parsedOther = self.paramsControlCore(**otherArgs)
        self.now: Union[QurryV3.argsMain, QurryV3.argsCore] = attributedDict(
            params={
                **self._expsConfig.make(),
                # ID of experiment.
                'expID': self.IDNow,
                # Qiskit argument of experiment.
                # Multiple jobs shared
                'shots': shots,
                'backend': backend,
                'provider': provider,
                'runConfig': runConfig,
                # Single job dedicated
                'runBy': 'gate' if isinstance(backend, IBMQBackend) else runBy,
                'decompose': decompose,
                'transpileArgs': transpileArgs,
                # Other arguments of experiment
                'drawMethod': drawMethod,
                'resultKeep': resultKeep,
                'dataRetrieve': dataRetrieve,
                'tags': tags,

                **parsedOther,
            },
            paramsKey=self._expsConfig.make().keys(),
        )
        self.exps[self.IDNow] = {
            **self._expsBase.make(),
            **self.now,
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
    def circuitMethod(self) -> list[QuantumCircuit]:
        """The method to construct circuit.
        Where should be overwritten by each construction of new measurement.

        Returns:
            Union[QuantumCircuit, list[QuantumCircuit]]:
                The quantum circuit of experiment.
        """

    def circuitMethod(self) -> list[QuantumCircuit]:

        argsNow: Union[QurryV3.argsMain, QurryV3.argsCore] = self.now
        circuit = self.waves[argsNow.wave]
        numQubits = circuit.num_qubits
        print(
            f"| Directly call: {self.now.wave} with sampling {argsNow.sampling}")

        return [circuit for i in range(argsNow.sampling)]

    def circuitBuild(
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
        circuitSet = self.circuitMethod()
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
        additionName: Optional[str] = None,
        saveLocation: Optional[Union[Path, str]] = None,
        excepts: list = [],
    ) -> dict[str, any]:
        """Export the experiment data, if there is a previous export, then will overwrite.

        - example of file.name:

            `{name}.{self.exps[expID]['expsName']}.expId={expID}.json`

        Args:
            expID (Optional[str], optional):
                The id of the experiment will be exported.
                If `expID == None`, then export the experiment which id is`.IDNow`.
                Defaults to `None`.

            additionName (Optional[str], optional):
                Extend file name.

                ```
                filename = (
                    Path(f"{additionName}.{self.exps[legacyId]['expsName']}.expId={legacyId}.json")
                ) if additionName else (
                    Path(f"{self.exps[legacyId]['expsName']}.expId={legacyId}.json")
                )
                self.exps[legacyId]['filename'] = filename
                ```
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
        if not legacyId:
            warnings.warn(
                f"No such expID '{expID}', waiting for legacy be written.")
            return {}

        # filename
        filename = (
            f"{additionName}.{self.exps[legacyId]['expsName']}.expId={legacyId}"
        ) if additionName else (
            f"{self.exps[legacyId]['expsName']}.expId={legacyId}"
        )
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
            carousel=[('dots', 20, 6), 'basic'],
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

                if not os.path.exists(saveLoc):
                    os.mkdir(saveLoc)

                self.exps[legacyId]['saveLocation'] = saveLoc
                legacyExport = jsonablize(exports)
                with open((saveLoc / (filename+'.json')), 'w+', encoding='utf-8') as Legacy:
                    json.dump(
                        legacyExport, Legacy, indent=2, ensure_ascii=False)

            elif saveLocation == None:
                legacyExport = jsonablize(exports)

            else:
                legacyExport = jsonablize(exports)
                warnings.warn(
                    "'saveLocation' is not the type of 'str' or 'Path', " +
                    "so export cancelled.")

        tales = self.exps[legacyId]['sideProduct']
        if len(tales) > 0:
            with Gajima(
                carousel=[('dots', 20, 6), 'basic'],
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

        if not os.path.exists(saveLocation):
            raise FileNotFoundError(f"Such location not found: {saveLocation}")

        legacyRead = {}
        if expID != None:
            lsfolder = glob.glob(str(saveLocation / f"*{expID}*.json"))
            if len(lsfolder) == 0:
                raise FileNotFoundError(f"The file 'expID={expID}' not found at '{saveLocation}'.")

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
            **{ k: v for k, v in legacyRead.items() if k not in excepts },
        }

        if isinstance(legacyRead, dict):
            if "tags" in legacyRead:
                legacyRead["tags"] = tuple(legacyRead["tags"]) if isinstance(
                    legacyRead["tags"], list) else legacyRead["tags"]

            if not self._expsBase.ready(legacyRead):
                lost = self._expsBase.check(legacyRead)
                print(f"Key Lost: {lost}")
        else:
            raise TypeError("The export file does not match the type 'dict'.")

        return legacyRead

    def circuitTranspiler(
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
        circuitSet = self.circuitBuild(**allArgs)
        argsNow = self.now

        # transpile
        circs = transpile(
            circuitSet if isinstance(circuitSet, list) else [circuitSet],
            backend=argsNow.backend,
            **argsNow.transpileArgs,
        )

        figTranspile = None
        with Gajima(
            carousel=[('dots', 20, 6), 'basic'],
            prefix="| ",
            desc="Transpile circuits",
            finish_desc="Transpile finished",
        ) as gajima:
            if isinstance(circs, QuantumCircuit):
                figTranspile = [self.drawCircuit(
                    expID=None,
                    circuitSet=circs,
                    drawMethod=argsNow.drawMethod,
                    decompose=argsNow.decompose,
                )]

            elif isinstance(circs, list):
                circuitSetLength = len(circs)
                figTranspile = [self.drawCircuit(
                    expID=None,
                    circuitSet=circs,
                    whichCircuit=i,
                    drawMethod=argsNow.drawMethod,
                    decompose=argsNow.decompose,
                ) for i in range(circuitSetLength)]

        self.exps[self.IDNow]['figTranspile'] = figTranspile
        return circs

    def run(
        self,
        **allArgs: any,
    ) -> Union[Result, ManagedResults]:
        """Export the result after running the job.
        - At same position with `self.retrieveOnly()` in the process.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.

        Returns:
            Union[Result, ManagedResults]: The result of the job.
        """
        circs = self.circuitTranspiler(**allArgs)
        argsNow = self.now

        execution = execute(
            circs,
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

    # def retrieve(
    #     self,
    #     **allArgs: any,
    # ) -> Optional[list[dict]]:
    #     """Retrieve the data from IBMQService which is already done, and add it into `self.exps`.

    #     Args:
    #         allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.

    #     Raises:
    #         KeyError: The necessary keys in `self.now.dataRetrieve` are lost.
    #             When the job record does not have `jobID`.
    #         ValueError: `argsNow.dataRetrieve` is null.

    #     Returns:
    #         Optional[list[dict]]: The result of the job.
    #     """

    #     argsNow = self.paramsControlCore(**allArgs)
    #     if not isinstance(argsNow.provider, AccountProvider):
    #         raise ValueError("Provider required.")

    #     retrievedBase = self._expsBase.make()

    #     if isinstance(argsNow.dataRetrieve, dict):
    #         lost = self._expsBase.check(argsNow.dataRetrieve)
    #         for k in lost:
    #             if k in ["jobID", "IBMQJobManager"]:
    #                 raise KeyError(
    #                     f"The giving data to retrieve jobs needs the key '{k}'")
    #         retrievedBase = argsNow.dataRetrieve

    #     elif isinstance(argsNow.dataRetrieve, str):
    #         retrievedBase["jobID"] = [argsNow.dataRetrieve]

    #     else:
    #         raise ValueError(
    #             "The giving data to retrieve jobs has to be 'str' of 'jobID' or 'dict' contained 'jobID'.")

    #     result = None
    #     for singleJobID in retrievedBase["jobID"]:
    #         try:
    #             retrieved = IBMQJobManager().retrieve_job_set(
    #                 job_set_id=singleJobID,
    #                 provider=argsNow.provider,
    #                 refresh=True
    #             )
    #             result = retrieved.results()

    #         except IBMQJobManagerUnknownJobSet as e:
    #             warnings.warn("Job unknown.", e)

    #         except IBMQJobManagerInvalidStateError as e:
    #             warnings.warn(
    #                 "Job faied by 'IBMQJobManagerInvalidStateError'", e)

    #         except JobError as e:
    #             warnings.warn("Job faied by 'JobError", e)

    #     self.exps[self.IDNow] = {
    #         **self.exps[self.IDNow],
    #         'expID': self.IDNow,
    #         'result': result,
    #         **retrievedBase,
    #     }

    #     return result

    @abstractclassmethod
    def quantity(cls) -> tuple[Quantity, Counts]:
        """Computing specific squantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            tuple[dict, dict]:
                Counts, purity, entropy of experiment.
        """
        ...

    @classmethod
    def quantity(
        cls,
        shots: int,
        result: Union[Result, ManagedResults],
        resultIdxList: Optional[list[int]] = None,
        sampling: int = 1,
        **otherArgs,
    ):
        """Computing specific squantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            tuple[dict, dict]:
                Counts, purity, entropy of experiment.
        """
        if resultIdxList == None:
            resultIdxList = [i for i in range(sampling)]
        else:
            ...

        counts = result.get_counts(resultIdxList[0])

        dummy = -100
        quantity = {
            '_dummy': dummy,
        }
        return counts, quantity

    def output(
        self,
        dataRetrieve: Optional[dict[Union[list[str], str]]] = None,
        withCounts: bool = False,
        __log: dict[str] = {},
        **allArgs: any,
    ) -> Union[Quantity, tuple[Quantity, Counts]]:
        """Export the result which completed calculating purity.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.

        Returns:
            dict[float]: The result.
        """
        print(f"+"+"-"*20+"\n"+f"| Calculating {self.__name__}...")

        # result = (self.retrieve if dataRetrieve != None else self.run)(
        #     dataRetrieve=dataRetrieve,
        #     **allArgs,
        # )
        result = self.run(
            dataRetrieve=dataRetrieve,
            **allArgs,
        )
        argsNow: Union[QurryV3.argsMain, QurryV3.argsCore] = self.now
        print(f"| name: {argsNow.expsName}\n"+f"| id: {self.IDNow}")

        counts, quantity = self.quantity(
            **argsNow,
            result=result,
        )

        if argsNow.resultKeep:
            warnings.warn(
                "Result will keep, but it may cause memory overallocated.")
            self.exps[self.IDNow]['result'] = result

        else:
            # print("| Quantity are figured out, result will clear.")
            del self.exps[self.IDNow]['result']

        for k in quantity:
            if k[0] == '_' and k != '_dummy':
                self.exps[self.IDNow]['sideProduct'][k[1:]] = quantity[k]
            if k == '_dummy':
                withCounts = True
                
        for k, v in __log.items():
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
        
    """ Multiple Outputs """
    def resourceCheck(self) -> None:
        """_summary_
        """
        self.resourceWatch()
        self.resourceWatch.report()

    def paramsControlMulti(
        self,
        # configList
        configList: list = [],
        # Configuration of `IBMQJobManager().run`
        # Multiple jobs shared
        shots: int = 1024,
        backend: Backend = AerProvider().get_backend('aer_simulator'),
        provider: AccountProvider = None,
        runConfig: dict = {},
        # IBMQJobManager() dedicated
        managerRunArgs: dict = {
            'max_experiments_per_job': 200,
        },
        # Other arguments of experiment
        # Multiple jobs shared
        jobsType: str = "multiJobs",
        isRetrieve: bool = False,
        expsName: str = 'exps',
        independentExports: bool = False,
        # `writeLegacy`
        additionName: Optional[str] = None,
        saveLocation: Union[Path, str] = Path('./'),

        **otherArgs: any,
    ) -> argsMultiMain:
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
            'additionName': 'export',
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

            runConfig (dict, optional):
                Configuration of :func:`qiskit.execute`.
                Defaults to `{}`.

            # IBMQJobManager() dedicated
            managerRunArgs (dict, optional):
                Configuration of :func:`IBMQJobManager().run`.
                Defaults to `{
                    'max_experiments_per_job': 200,
                }`.

            # Other arguments of experiment
            jobType (str, optional):
                The type name of the jobs.
                Defaults to `"multiJobs"`.

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

            additionName (Optional[str], optional):
                Extend file name.

                ```
                filename = (
                    Path(f"{additionName}.{self.exps[legacyId]['expsName']}.expId={legacyId}.json")
                ) if additionName else (
                    Path(f"{self.exps[legacyId]['expsName']}.expId={legacyId}.json")
                )
                self.exps[legacyId]['filename'] = filename
                ```
                Defaults to `None`.

            saveLocation (Optional[Union[Path, str]], optional):
                Where to save the export content as `json` file.
                If `saveLocation == None`, then cancelled the file to be exported.
                Defaults to `None`.

        - example of file.name:

            `{name}.{self.exps[expID]['expsName']}.expId={expID}.json`

            otherArgs (any):
                Other arguments includes the variants of experiment.

        Returns:
            attributedDict: Current arguments.
        """

        # naming
        print(f"| Naming...")
        indexRename = 1
        rjustLen = 3
        if isRetrieve:
            immutableName = expsName
            exportLocation = Path(saveLocation) / immutableName
            print(
                f"| Retrieve {immutableName}...\n" +
                f"| at: {exportLocation}"
            )

        else:
            expsName = f'{expsName}.{self.shortName}'
            rjustLen = 3 if int(np.log10(indexRename)) + \
                2 <= 3 else int(np.log10(indexRename))+2
            immutableName = f"{expsName}.{str(indexRename).rjust(rjustLen, '0')}"
            exportLocation = Path(saveLocation) / immutableName
            while os.path.exists(exportLocation):
                print(f"| {exportLocation} is repeat name.")
                indexRename += 1
                immutableName = f"{expsName}.{str(indexRename).rjust(rjustLen, '0')}"
                exportLocation = Path(saveLocation) / immutableName
            print(
                f"| Write {immutableName}...\n" +
                f"| at: {exportLocation}"
            )
            os.makedirs(exportLocation)

        # configList
        initedConfigList = []
        for expIndex, config in enumerate(configList):
            initedConfigList.append(self._expsConfig.make({
                **config,
                'shots': shots,
                'backend': backend,
                'provider': provider,

                'expsName': expsName,
                'additionName': additionName,
                'saveLocation': Path(saveLocation),
                'exportLocation': exportLocation,

                'expIndex': expIndex,
            }))

        # pendingTags
        pendingTags = [expsName, additionName]

        # dataRetrieve
        powerJobID = None
        if isinstance(isRetrieve, str):
            powerJobID = isRetrieve
        elif isinstance(isRetrieve, dict):
            ...

        # gitignore
        gitignore = syncControl()

        self.multiNow: QurryV3.argsMultiMain = attributedDict(
            params=sortHashableAhead({
                **self._expsMultiConfig.make(),
                **otherArgs,

                # Configuration of `IBMQJobManager().run`
                # Multiple jobs shared
                'shots': shots,
                'backend': backend,
                'provider': provider,
                'runConfig': runConfig,

                # IBMQJobManager() dedicated
                'powerJobID': powerJobID,
                'managerRunArgs': managerRunArgs,

                # Other arguments of experiment
                # Multiple jobs shared
                'isRetrieve': isRetrieve,
                'expsName': immutableName,

                # Multiple job dedicated
                # 'pendingTags': pendingTags,
                # ? pendingTags works uncorrectly, check contain and type
                # ? by IBMQJobManagerInvalidStateError: 'job_tags needs to be a list or strings.'
                'independentExports': independentExports,
                
                'type': jobsType,
                'state': 'init',
                
                # configList
                'configList': initedConfigList,

                # `writeLegacy`
                'additionName': additionName,
                'saveLocation': Path(saveLocation),
                'exportLocation': exportLocation,

                'gitignore': gitignore,
                'listExpID': [],  # expIDList
                'listFile': [],  # fileList
                # 'listQuantity': [],  # expPurityList/expEntropyList
                'tagMapExpsID': TagMap(),  # expsBelong
                'tagMapIndex': TagMap(),

                'tagMapQuantity': TagMap(),
                'tagMapCounts': TagMap(),

                'circuitsMap': {},
                'circuitsNum': {},

            }),
            paramsKey=self._expsMultiConfig.make().keys(),
        )

        return self.multiNow
        
    JobManager = IBMQJobManager()
    """:meth:`IBMQJobManager()` in :cls:`qurry`"""    

    def multiOutput(
        self,
        configList: list = [],
        shots: int = 1024,
        backend: Backend = AerProvider().get_backend('aer_simulator'),

        expsName: str = 'exps',
        independentExports: bool = False,
        additionName: Optional[str] = None,
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
        argsMulti = self.paramsControlMulti(
            configList=configList,
            shots=shots,
            backend=backend,

            expsName=expsName,
            independentExports=independentExports,
            additionName=additionName,
            saveLocation=saveLocation,

            **allArgs
        )

        print(f"| MultiOutput {self.__name__} Start...\n"+f"+"+"-"*20)
        numConfig = len(argsMulti.configList)
        for config in argsMulti.configList:
            print(
                f"| index={config['expIndex']}/{numConfig} - {round(time.time() - start_time, 2)}s")
            quantity, counts = self.output(
                **config,
                withCounts=True,
                __log={
                    'time': time.time() - start_time,
                    'memory': self.resourceWatch.virtual_memory().percent
                }
            )

            # resource check
            self.resourceCheck()

            # legacy writer
            legacy = self.writeLegacy(
                saveLocation=argsMulti.exportLocation,
                expID=self.IDNow,
                additionName=argsMulti.additionName,
            )
            legacyTag = tuple(legacy['tags']) if isinstance(
                legacy['tags'], list) else legacy['tags']
            
            argsMulti.logTime.append(round(time.time() - start_time, 2))
            argsMulti.logRAM.append(self.resourceWatch.virtual_memory().percent)

            for k in ['all', 'noTags']:
                if legacyTag == k:
                    legacyTag == None
                    print(
                        f"| warning: '{k}' is a reserved key for export data.")

            # packing
            argsMulti.listFile.append(legacy['filename'])
            argsMulti.listExpID.append(self.IDNow)
            
            argsMulti.tagMapExpsID.guider(legacyTag, self.IDNow)
            argsMulti.tagMapIndex.guider(legacyTag, config['expIndex'])
            argsMulti.tagMapQuantity.guider(legacyTag, quantity)
            argsMulti.tagMapCounts.guider(legacyTag, counts)

        print(f"| Export...")
        argsMulti.gitignore.ignore('*.json')
        argsMulti.state = 'completed'
        dataMultiJobs = argsMulti._jsonize()

        for n, data in [
            ('multiJobs.json', dataMultiJobs),
            ('tagMapQuantity.json', argsMulti.tagMapQuantity),
            ('tagMapCounts.json', argsMulti.tagMapCounts),
        ]:
            argsMulti.gitignore.sync(f'*.{n}')
            print(f"| Export {n}")
            quickJSONExport(
                content=data,
                filename=argsMulti.exportLocation /
                f"{argsMulti.expsName}.{n}",
                mode='w+',
                jsonablize=True)

        if argsMulti.independentExports:
            print(f"| independentExports...")
            for n in [
                'listExpID',
                'listFile',
                'tagMapExpsID',
                'tagMapIndex'
            ]:
                argsMulti.gitignore.sync(f'*.{n}.json')
                print(f"| Export {n}.json")
                quickJSONExport(
                    content=argsMulti[n],
                    filename=argsMulti.exportLocation /
                    f"{argsMulti.expsName}.{n}.json",
                    mode='w+',
                    jsonablize=True)

        argsMulti.gitignore.export(argsMulti.exportLocation)
        argsMulti.logTime.export(argsMulti.exportLocation, 'Time.log')
        argsMulti.logRAM.export(argsMulti.exportLocation, 'RAM.log')
        gc.collect()
        print(
            f"| MultiOutput {self.__name__} End in {round(time.time() - start_time, 2)} sec ...\n" +
            f"+"+"-"*20)

        return dataMultiJobs

    def multiRead(
        self,
        exportName: Union[Path, str],
        saveLocation: Union[Path, str] = './',
        **allArgs: any,
    ) -> dict[any]:
        """Require to read the file exported by `.powerJobsPending`.

        Args:
            exportName (Union[Path, str]):
                The folder name of the job wanted to import.

            isRetrieve (bool, optional):
                Whether to retrieve the experiment date.
                Defaults to `True`.

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
        start_time = time.time()
        argsMulti = self.paramsControlMulti(
            saveLocation=saveLocation,
            expsName=exportName,
            isRetrieve=True,
            **allArgs,
        )
        dataDummyJobs: dict[any] = {}
        print(f"| MultiRead {self.__name__} Start...\n"+f"+"+"-"*20)

        if (exportName == None):
            raise ValueError("'exportName' required.")
        if not os.path.exists(Path(saveLocation)):
            raise FileNotFoundError(f"'{saveLocation}' does not exist.")
        if not os.path.exists(Path(saveLocation) / exportName):
            raise FileNotFoundError(
                f"'{Path(saveLocation) / exportName}' does not exist, " +
                "exportName may be wrong or not in this folder.")

        dataPowerJobsName = argsMulti.exportLocation / \
            f"{argsMulti.expsName}.multiJobs.json"
        dataMultiJobsName = argsMulti.exportLocation / \
            f"{argsMulti.expsName}.powerJobs.json"
        if os.path.exists(dataPowerJobsName):
            argsMulti['type'] = 'powerJobs'
            with open(dataPowerJobsName, 'r', encoding='utf-8') as theData:
                dataDummyJobs = json.load(theData)

            for k in ['powerJobID', ['circuitsMap', 'circsMapDict']]:
                if isinstance(k, list):
                    for l in k+[None]:
                        if l in dataDummyJobs:
                            break
                        elif l == None:
                            raise ValueError(
                                f"File broken due to lost one of {l}.")

                elif not k in dataDummyJobs:
                    raise ValueError(f"File broken due to lost {k}.")

            if 'circsMapDict' in dataDummyJobs:
                dataDummyJobs['circuitsMap'] = dataDummyJobs['circsMapDict'].copy()

        elif os.path.exists(dataMultiJobsName):
            with open(dataMultiJobsName, 'r', encoding='utf-8') as theData:
                dataDummyJobs = json.load(theData)

        else:
            for n in [
                'listExpID',
                'listFile',
                'tagMapExpsID',
                'tagMapIndex',
                'tagMapQuantity',
                'tagMapCounts',
            ]:
                with open(
                        argsMulti.exportLocation /
                    f"{argsMulti.expsName}.{n}.json",
                        'r', encoding='utf-8') as File:
                    dataDummyJobs[n] = json.load(File)

            if os.path.exists(
                    argsMulti.exportLocation / f"{argsMulti.expsName}.powerJobID.csv"):
                with open(
                        argsMulti.exportLocation / f"{argsMulti.expsName}.powerJobID.csv", 'r', encoding='utf-8') as File:
                    content = File.readlines()
                    dataDummyJobs['powerJobID'] = content[0][:-1]

        # for n in [
        #     'tagMapExpsID',
        #     'tagMapIndex',
        #     'tagMapQuantity',
        #     'tagMapCounts',
        # ]:
            # if n in dataDummyJobs:
        for tmk in [k for k in dataDummyJobs.keys() if 'tagMap' in k]:
            dataDummyJobs[tmk] = keyTupleLoads(dataDummyJobs[tmk])
        
        # TODO: remake multiRead
        if dataDummyJobs['state'] == "completed":
            for n in [    
                'tagMapQuantity',
                'tagMapCounts',
            ]:
                with open(
                        argsMulti.exportLocation /
                    f"{argsMulti.expsName}.{n}.json",
                        'r', encoding='utf-8') as File:
                    dataDummyJobs[n] = json.load(File)
            
        if dataDummyJobs['saveLocation'] != argsMulti.saveLocation:
            dataDummyJobs['saveLocation'] = argsMulti.saveLocation

        gc.collect()
        print(
            f"| MultiRead {self.__name__} End in {round(time.time() - start_time, 2)} sec ...\n"+f"+"+"-"*20)

        return dataDummyJobs
    
    @staticmethod
    def reportCounts(JobManager: IBMQJobManager) -> dict[str, int]:
        """A better report representation of :meth:`IBMQJobManager().report()`

        Args:
            JobManager (IBMQJobManager): A :cls:`IBMQJobManager` object.

        Returns:
            dict[str, int]: Counts of report status.
        """
        job_set_statuses = [job_set.statuses() for job_set in JobManager._job_sets]
        status_list = [stat for stat_list in job_set_statuses for stat in stat_list]

        statusCounter = Counter(status_list)
        status_counts = {
            'Total': len(status_list),
            'Successful': statusCounter[JobStatus.DONE],
            'Failed': statusCounter[JobStatus.ERROR],
            'Cancelled': statusCounter[JobStatus.CANCELLED],
            'Running': statusCounter[JobStatus.RUNNING],
            'Initializing': statusCounter[JobStatus.INITIALIZING],
            'Validating': statusCounter[JobStatus.VALIDATING],
            'Queued': statusCounter[JobStatus.QUEUED],
        }

        return status_counts
        

    def powerPending(
        self,
        configList: list = [],
        **allArgs: any,
    ) -> dict[any]:
        """Require to read the file exported by `.powerJobsPending`.

        https://github.com/Qiskit/qiskit-terra/issues/4778
        According to this issue, `IBMQJobManager` will automatically splits off job to fit the backend limit
        and combines the result, so this version `jobOnly` will ignore the problem on the number of jobs
        larger than backends limits.

        Args:
            allArgs: all arguments will handle by `.paramsControlMulti()` and export as specific format.

        Returns:
            dict[any]: All result of jobs.
        """
        start_time = time.time()
        argsMulti = self.paramsControlMulti(
            **allArgs,
            jobsType='powerJobs',
            configList=configList,
        )
        pendingArray = []
        allTranspliedCircs = {}

        print(f"| PowerPending {self.__name__} Start...\n"+f"+"+"-"*20)
        numConfig = len(argsMulti.configList)
        for config in argsMulti.configList:
            print(
                f"| index={config['expIndex']}/{numConfig} - {round(time.time() - start_time, 2)}s")
            circuitSet = self.circuitTranspiler(**config)
            allTranspliedCircs[self.IDNow] = circuitSet
            
            # resource check
            self.resourceCheck()

            # circuit numbers
            if isinstance(circuitSet, list):
                numCirc = len(circuitSet)
            elif isinstance(circuitSet, QuantumCircuit):
                numCirc = 1
            else:
                numCirc = 0
                warnings.warn(
                    f"The circuit output of '{self.IDNow}' is nor 'list' neither 'QuantumCircuit' " +
                    f"but '{type(circuitSet)}'.")
            argsMulti.circuitsNum[self.IDNow] = numCirc

            # legacy writer
            legacy = self.writeLegacy(
                saveLocation=argsMulti.exportLocation,
                expID=self.IDNow,
                additionName=argsMulti.additionName,
            )
            legacyTag = tuple(legacy['tags']) if isinstance(
                legacy['tags'], list) else legacy['tags']

            for k in ['all', 'noTags']:
                if legacyTag == k:
                    legacyTag == None
                    print(
                        f"| warning: '{k}' is a reserved key for export data.")

            argsMulti.listFile.append(legacy['filename'])
            argsMulti.listExpID.append(self.IDNow)

            argsMulti.tagMapExpsID.guider(legacyTag, self.IDNow)
            argsMulti.tagMapIndex.guider(legacyTag, config['expIndex'])

        with Gajima(
            enumerate(argsMulti.listExpID),
            carousel=[('dots', 20, 6), 'basic'],
            prefix="| ",
            desc="Packing circuits for pending",
            finish_desc="Packing Completed",
        ) as gajima:
            for expIndex, expIDKey in gajima:
                argsMulti.circuitsMap[expIDKey] = []
                tmpCircuitNum = argsMulti.circuitsNum[expIDKey]
                gajima.gprint(
                    f"| Packing expID: {expIDKey}, index={expIndex} with {tmpCircuitNum} circuits ...")

                for i in range(tmpCircuitNum):
                    argsMulti.circuitsMap[expIDKey].append(
                        len(pendingArray))
                    if not isinstance(allTranspliedCircs[expIDKey][i], QuantumCircuit):
                        print(allTranspliedCircs[expIDKey][i], i)
                        raise ValueError("Critical Error")
                    pendingArray.append(allTranspliedCircs[expIDKey][i])

        with Gajima(
            carousel=[('dots', 20, 6), 'basic'],
            prefix="| ",
            desc="Pending Jobs",
            finish_desc="Pending finished and Exporting",
        ) as gajima:
            powerJob = self.JobManager.run(
                **argsMulti.managerRunArgs,
                experiments=pendingArray,
                backend=argsMulti.backend,
                shots=argsMulti.shots,
                name=f'{argsMulti.expsName}_w/_{len(pendingArray)}_jobs',
                # job_tags=argsMulti.pendingTags
                # ? waiting for the issue of contain
            )
            gajima.gprint(f"| report:", self.JobManager.report())
            powerJobID = powerJob.job_set_id()
            gajima.gprint(f"| name: {powerJob.name()}")
            argsMulti.powerJobID = powerJobID
            argsMulti.state = 'pending'
            
            # ! Too many request
            # gajima.gprint(f"| Waiting for all jobs be queued... ")
            # isQueued = False
            # waiting = 0
            
            # tiks = 20 # TODO: as a configure
            # givenUp = 1800
            # refreshPoint = 600
            # while not isQueued:
            #     waiting += tiks
            #     time.sleep(tiks)
            #     DoubleChecker = IBMQJobManager()
            #     if waiting > givenUp:
            #         print(f"| Pending may be failed, given up waiting.")
            #         argsMulti.state = 'failed'
            #         break
            #     try:
            #         test = DoubleChecker.retrieve_job_set(
            #             job_set_id=argsMulti.powerJobID,
            #             provider=argsMulti.backend.provider(),
            #             refresh=waiting%refreshPoint == 0,
            #         )
            #         isQueued = True
            #         gajima.gprint(f"| All jobs are queued, continuing to export. ")
            #         statusCounts = self.reportCounts(JobManager)
            #         gajima.gprint(f"| status: {statusCounts}")
            #     except IBMQJobManagerUnknownJobSet as e:
            #         isQueued = False
            
            # powerJobsIDList = [mj.job.job_id() for mj in powerJob.jobs()]
            
        argsMulti.gitignore.ignore('*.json')
        argsMulti.gitignore.sync(f'*.powerJobs.json')

        dataPowerJobs = argsMulti._jsonize()
        quickJSONExport(
            content=dataPowerJobs,
            filename=argsMulti.exportLocation /
            f"{argsMulti.expsName}.powerJobs.json",
            mode='w+',
            jsonablize=True)

        with open(
                argsMulti.exportLocation /
            f"{argsMulti.expsName}.powerJobID.csv",
                'w+', encoding='utf-8') as theFile:
            print(f"{powerJobID}", file=theFile)
        print(f"| Export powerJobID.csv")

        if argsMulti.independentExports:
            print(f"| independentExports...")
            for n in [
                'listExpID',
                'listFile',
                'tagMapExpsID',
                'tagMapIndex',
                'circuitsMap',
                'circuitsNum',
            ]:
                argsMulti.gitignore.sync(f'*.{n}.json')
                print(f"| Export {n}.json")
                quickJSONExport(
                    content=argsMulti[n],
                    filename=argsMulti.exportLocation /
                    f"{argsMulti.expsName}.{n}.json",
                    mode='w+',
                    jsonablize=True)

        argsMulti.gitignore.export(argsMulti.exportLocation)

        gc.collect()
        print(
            f"| PowerPending {self.__name__} End in {round(time.time() - start_time, 2)} sec ...\n" +
            f"+"+"-"*20)

        return dataPowerJobs

    def powerOutput(
        self,
        exportName: Union[Path, str],
        saveLocation: Union[Path, str] = './',
        overwrite: bool = False,
        **allArgs: any,
    ) -> dict[any]:
        """Require to read the file exported by `.powerJobsPending`.

        Args:
            exportName (Union[Path, str]):
                The folder name of the job wanted to import.
            isRetrieve (bool, optional):
                Whether to collect results from IBMQ via `IBMQJobManager`.
                Defaults to False.
            powerJobID (str, optional):
                Job Id. Defaults to ''.
            provider (Optional[AccountProvider], optional):
                The provider of the backend used by job.
                Defaults to None.
            saveLocation (Union[Path, str], optional):
                The location of the folder of the job wanted to import.
                Defaults to './'.

            allArgs: all arguments will handle by `.paramsControlMulti()` and export as specific format.

        Raises:
            ValueError: When file is broken.

        Returns:
            dict[any]: All result of jobs.
        """

        start_time = time.time()
        dataPowerJobs = self.multiRead(
            exportName=exportName,
            dataRetrieve=True,
            saveLocation=saveLocation,
            **allArgs,
        )
        argsMulti: self.argsMultiMain = self.multiNow

        print(f"| PowerOutput {self.__name__} Start...\n"+f"+"+"-"*20)
        if dataPowerJobs['type'] == 'multiJobs':
            print(
                f"| PowerOutput {self.__name__} End " +
                f"with reading a multiJobs in {time.time() - start_time} sec ...\n" +
                f"+"+"-"*20)
            return dataPowerJobs

        if dataPowerJobs['state'] == 'pending':
            print(f"| Retrieve result...")
            powerJob = self.JobManager.retrieve_job_set(
                job_set_id=dataPowerJobs['powerJobID'],
                provider=argsMulti.provider,
            )

        elif overwrite and isinstance(overwrite, bool):
            print(f"| Overwrite activate and retrieve result...")
            powerJob = self.JobManager.retrieve_job_set(
                job_set_id=dataPowerJobs['powerJobID'],
                provider=argsMulti.provider,
            )

        else:
            print(
                f"| PowerOutput {self.__name__} End " +
                "with loading completed powerJobs in {time.time() - start_time} sec ...\n" +
                f"+"+"-"*20)
            return dataPowerJobs

        argsMulti['gitignore'] = syncControl(dataPowerJobs['gitignore'])
        with Gajima(
            carousel=[('dots', 20, 6), 'basic'],
            prefix="| ",
            desc="Dealing results",
        ) as gajima:
            powerResult: ManagedResults = powerJob.results()

        idxNum = 0
        numConfig = len(dataPowerJobs['listExpID'])
        for expIDKey in dataPowerJobs['listExpID']:
            print(
                f"| index={idxNum}/{numConfig} - {round(time.time() - start_time, 2)}s")
            self.exps[expIDKey] = self.readLegacy(
                expID=expIDKey,
                # TODO: make it better
                # saveLocation=Path(dataPowerJobs['exportLocation']),
                saveLocation=Path(argsMulti.exportLocation),
            )

            # output
            counts, quantityWSideProduct = self.quantity(**{
                **self.exps[expIDKey],
                'result': powerResult,
                'resultIdxList': dataPowerJobs['circuitsMap'][expIDKey],
            })

            for k in quantityWSideProduct:
                if k[0] == '_' and k != '_dummy':
                    self.exps[expIDKey]['sideProduct'][k[1:]
                                                       ] = quantityWSideProduct[k]

            quantity = {k: quantityWSideProduct[k]
                        for k in quantityWSideProduct if k[0] != '_'}
            self.exps[expIDKey] = {
                **self.exps[expIDKey],
                **quantity,
                'counts': counts,
            }

            # legacy writer
            legacy = self.writeLegacy(
                saveLocation=Path(argsMulti.exportLocation),
                expID=expIDKey,
                additionName=dataPowerJobs['additionName'],
            )
            legacyTag = tuple(legacy['tags']) if isinstance(
                legacy['tags'], list) else legacy['tags']

            for k in ['all', 'noTags']:
                if legacyTag == k:
                    legacyTag == None
                    print(
                        f"| warning: '{k}' is a reserved key for export data.")

            argsMulti.tagMapQuantity.guider(legacyTag, quantity)
            argsMulti.tagMapCounts.guider(legacyTag, counts)

            print(f"| index={idxNum} end...\n"+f"+"+"-"*20)
            idxNum += 1

        print(f"| Export...")
        argsMulti.gitignore.ignore('*.json')
        dataPowerJobs['state'] = 'completed'
        dataPowerJobs = jsonablize(dataPowerJobs)

        for n, data in [
            ('powerJobs.json', dataPowerJobs),
            ('tagMapQuantity.json', argsMulti.tagMapQuantity),
            ('tagMapCounts.json', argsMulti.tagMapCounts),
        ]:
            argsMulti.gitignore.sync(f'*.{n}')
            print(f"| Export {n}")
            quickJSONExport(
                content=data,
                filename=Path(argsMulti.exportLocation) /
                f"{dataPowerJobs['expsName']}.{n}",
                mode='w+',
                jsonablize=True)

        if argsMulti.independentExports:
            print(f"| independentExports...")
            for n in [
                'tagMapQuantity',
                'tagMapIndex'
            ]:
                argsMulti.gitignore.sync(f'*.{n}.json')
                print(f"| Export {n}.json")
                quickJSONExport(
                    content=dataPowerJobs[n],
                    filename=Path(argsMulti.exportLocation) /
                    f"{dataPowerJobs['expsName']}.{n}.json",
                    mode='w+',
                    jsonablize=True)

        argsMulti.gitignore.export(Path(argsMulti.exportLocation))
        gc.collect()
        print(
            f"| PowerOutput {self.__name__} End in {round(time.time() - start_time, 2)} sec ...\n"+f"+"+"-"*20)

        dataPowerJobs['result'] = powerResult
        return dataPowerJobs

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

    """ Close the export of __dict__ for it is too large."""
    # def to_dict(self) -> None:
    #     return self.__dict__
