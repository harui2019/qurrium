from qiskit import (
    Aer, execute, transpile,
    QuantumRegister, ClassicalRegister, QuantumCircuit
)

from qiskit.quantum_info import Operator
from qiskit.circuit.gate import Gate
from qiskit.circuit.instruction import Instruction
from qiskit.result import Result
from qiskit.providers import Backend, JobError, JobStatus
from qiskit.providers.ibmq import IBMQBackend
from qiskit.providers.ibmq.managed import (
    IBMQJobManager,
    # ManagedJobSet,
    # ManagedJob,
    ManagedResults,
    IBMQManagedResultDataNotAvailable,
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
    argdict,
    argTuple,
    syncControl,
    jsonablize,
    quickJSONExport,
    keyTupleLoads,
    sortHashableAhead,
    TagMap,
)
from .exceptions import UnconfiguredWarning
from .type import (
    TagMapType,
    Quantity,
    Counts,
    waveGetter,
    waveReturn,
)

# Qurry V0.4.0 - a Qiskit Macro

def defaultCircuit(numQubit: int) -> QuantumCircuit:
    return QuantumCircuit(
        numQubit, numQubit, name=f'qurry_default_{numQubit}')

class Qurry:
    """Qurry V0.4.0
    The qiskit job tool
    """
    __version__ = (0,4,0)

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
        backend: Backend = Aer.get_backend('aer_simulator')
        provider: Optional[AccountProvider] = None
        runArgs: dict = {}

        # Single job dedicated
        runBy: str = "gate"
        decompose: Optional[int] = 2
        transpileArgs: dict = {}

        # Other arguments of experiment
        drawMethod: str = 'text'
        resultKeep: bool = False
        expsName: str = 'exps'
        tags: Optional[Hashable] = None
        
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

    def expsBase(
        self,
        name: str = 'qurryExpsBase',
        defaultArg: dict = {
            # Arguments of experiment.
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
                **self.now._asdict(),
                **self.expsMain._asdict(),
            },
        )

    def expsBaseExcepts(
        self,
        excepts: list[str] = ['sideProduct', 'tagMapResult'],
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
        # configList
        configList: list = []

        # Configuration of `IBMQJobManager().run`
        # Multiple jobs shared
        shots: int = 1024
        backend: Backend = Aer.get_backend('aer_simulator')
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

    class expsMultiMain(NamedTuple):
        gitignore: syncControl = syncControl()
        listExpID: list = []
        listFile: list = []

        tagMapExpsID: TagMapType[str] = TagMap()
        tagMapFiles: TagMapType[str] = TagMap()
        tagMapIndex: TagMapType[Union[str, int]] = TagMap()
        tagMapQuantity: TagMapType[Quantity] = TagMap()
        tagMapCounts: TagMapType[Counts] = TagMap()
        # tagMapResult: TagMapType[Result] = TagMap()

        circuitsMap: dict = {}
        circuitsNum: dict = {}

        jobsType: str = "multiJobs"
        state: str = "init"
        
    def expsMultiBase(
        self,
        name: str = 'qurryMultiBase',
        defaultArg: dict = {
            # Arguments of experiment.
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
                **self.now._asdict(),
                **self.expsMain._asdict(),
            },
        )

    # TODO: make hint available in qurry

    def expsHint(
        self,
        name: str = 'qurryBaseHint',
        hintContext: dict = {
            "_basicHint": "This is a hint of qurry.",
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
                    "_basicHint": "This is a hint of qurry.",
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
        """Configuration to Initialize Qurry.

        Returns:
            dict[str, any]: The basic configuration of `Qurry`.
        """

    def initialize(self) -> dict[str, any]:

        self._expsBase = self.expsBase()
        self._expsHint = self.expsHint()
        self.shortName = 'qurry'
        self.__name__ = 'Qurry'

        return self._expsConfig, self._expsBase,

    def __init__(
        self,
        waves: Union[QuantumCircuit, list[QuantumCircuit]] = defaultCircuit(4),
    ) -> None:
        """The initialization of Qurry.

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
        self.expsMulti = argdict(
            params=self.expsMultiMain._asdict()
        ) # reresh per execution.
        self.jobManager = IBMQJobManager()
        
        # TODO: add params control
        self.resourceWatch = ResoureWatch()

        # namedtuple prototype
        self.namedtupleNow = namedtuple(
            typename='qurryArguments',
            field_names=self.argsMain._fields+self.argsCore._fields,
        )
        self.namedtupleMultiNow = namedtuple(
            typename='qurryMultiExpArgs',
            field_names=self.argsMain._fields+self.argsCore._fields,
        )

        # For reading arguments.
        self.now: Union[Qurry.argsMain, Qurry.argsCore] = self.namedtupleNow(**{ 
            **self.argsCore()._asdict(), **self.argsMain()._asdict()
        })
        self.IDNow = ''
        self.multiNow: Qurry.argsMultiMain = self.namedtupleMultiNow(
            **self.argsMultiMain._asdict()
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

    def waveCall(
        self,
        wave: Union[list[Hashable], Hashable, None] = None,
        runBy: Optional[Literal['gate', 'operator', 'instruction', 'copy']] = None,
        backend: Optional[Backend] = Aer.get_backend('aer_simulator'),
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
                Defaults to Aer.get_backend('aer_simulator').

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
        backend: Backend = Aer.get_backend('aer_simulator'),
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
            'backend': Aer.get_backend('aer_simulator'),
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
                Defaults to `Aer.get_backend('aer_simulator')`.

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
            argdict: Current arguments.
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
            
        # TODO: add params control
        self.resourceWatch = ResoureWatch(
            **otherArgs
        )

        # Export all arguments
        parsedOther = self.argsCore(
           **self.paramsControlCore(**otherArgs)
        )
        self.now: Union[Qurry.argsMain, Qurry.argsCore] = self.namedtupleNow(**{ 
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
            
            **parsedOther,
        })
        self.exps[self.IDNow] = {
            **self.now,
            **self._expsBase.make(),
        }

        return self.now
    
    @abstractmethod
    def method(self) -> list[QuantumCircuit]:
        """The method to construct circuit.
        Where should be overwritten by each construction of new measurement.

        Returns:
            Union[QuantumCircuit, list[QuantumCircuit]]:
                The quantum circuit of experiment.
        """

    def method(self) -> list[QuantumCircuit]:

        argsNow: Union[Qurry.argsMain, Qurry.argsCore] = self.now
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
        circuitSet = self.circuitMethod() if hasattr(self, 'circuitMethod') else self.method()
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
        _isMulti: bool = False,
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
        if legacyId == None:
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
            saveLocation = saveLocation / 'legacy'
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
        circuitSet = self.circuitBuild(**allArgs)
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
        circs = self.circuitTranspiler(**allArgs)
        argsNow = self.now

        execution = execute(
            circs,
            backend=argsNow.backend,
            shots=argsNow.shots,
            **argsNow.runArgs,
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
    def counts(cls) -> Counts:
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
        counts: Counts,
        num: int = 1,
        **otherArgs,
    ):
        
        dummy = -100
        quantity = {
            '_dummy': dummy,
            'sampling': num,
        }
        return counts, quantity
    
    """ Output single """
    
    def output(
        self,
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
        
        result = self.run(**allArgs,)
        argsNow: Union[Qurry.argsMain, Qurry.argsCore] = self.now
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
        
    """ Execution Multiple """
    
    def resourceCheck(self) -> None:
        """_summary_
        """
        self.resourceWatch()
        self.resourceWatch.report()
        
    # def pending(self):