from qiskit import (
    Aer, execute, transpile,
    QuantumRegister, ClassicalRegister, QuantumCircuit
)

from qiskit.quantum_info import Operator
from qiskit.circuit.gate import Gate
from qiskit.result import Result
from qiskit.providers import Backend, JobError
from qiskit.providers.ibmq import IBMQBackend
from qiskit.providers.ibmq.managed import (
    IBMQJobManager,
    # ManagedJobSet,
    # ManagedJob,
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
import time
import os
from math import pi
from uuid import uuid4
from pathlib import Path
from typing import Union, Optional, NamedTuple, overload
from abc import abstractmethod

from ..tool import (
    Configuration,
    argdict,
    syncControl,
    jsonablize,
    quickJSONExport,
    keyTupleLoads,
    Gajima,
)
from .exceptions import UnconfiguredWarning
from .type import (
    TagKeysAllowable,
    TagMapExpsIDType,
    TagMapIndexType,
    TagMapQuantityType,
    TagMapCountsType,
    Quantity,
    Counts,
)

# Qurry V0.3.0 - a Qiskit Macro


def defaultCircuit(numQubit: int) -> QuantumCircuit:
    return QuantumCircuit(numQubit)


"""

_expsConfig = expsConfig(
    name='dummyConfig',
    defaultArg={
        'wave': None,
        'dummy': None,
    },
)
_expsBase = expsBase(
    name='dummyBase',
    expsConfig= _expsConfig,
    defaultArg={
        'dummyResult1': None,
        'dummyResult2': None,
    },
)
_expsMultiConfig = expsConfigMulti(
    name='dummyConfigMulti',
    expsConfig= _expsConfig,
    defaultArg={
        'dummyMultiVariaint1': None,
        'dummyMultiVariaint2': None,
    },
)
_expsHint = expsHint(
    name: str = 'qurryBaseHint',
    expsConfig = _expsBase,
    hintContext = {
        'dummyResult1': 'This is dummyResult1.',
        'dummyResult2': 'This is dummyResult2.',
    },
)
"""


class Qurry:
    """Qurry V0.3.1
    The qiskit job tool
    """

    """ Configuration """

    class argdictCore(NamedTuple):
        expsName: str = 'exps',
        wave: Union[QuantumCircuit, any, None] = None,
        sampling: int = 1,

    class argdictNow(argdictCore):
        # ID of experiment.
        expID: Optional[str] = None,

        # Qiskit argument of experiment.
        # Multiple jobs shared
        shots: int = 1024,
        backend: Backend = Aer.get_backend('qasm_simulator'),
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
        expsName: str = 'exps',
        tags: Optional[TagKeysAllowable] = None,

    def expsConfig(
        self,
        name: str = 'qurryConfig',
        defaultArg: dict[any] = {
            **argdictCore()._asdict()
        },
    ) -> Configuration:
        """The default format and value for executing a single experiment.
        - Example:

        ```
        {
            # ID of experiment.
            'expID': None,

            # Variants of experiment.
            **defaultArg,

            # Qiskit argument of experiment.
            # Multiple jobs shared
            'shots': 1024,
            'backend': Aer.get_backend('qasm_simulator'),
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
            Configuration: _description_
        """
        return Configuration(
            name=name,
            default={
                **self.argdictNow()._asdict(),
                # Variants of experiment.
                **defaultArg,
            },
        )

    def expsBase(
        self,
        name: str = 'qurryExpsBase',
        defaultArg: dict = {
            # Reault of experiment.
        },
    ) -> Configuration:
        """The default storage format and values of a single experiment.
        - Example:

        ```
        {
            # ID of experiment.
            'expID': None,

            # Variants of experiment.
            **defaultArg,

            # Qiskit argument of experiment.
            # Multiple jobs shared
            'shots': 1024,
            'backend': Aer.get_backend('qasm_simulator'),
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
            Configuration: _description_
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

    class argdictMultiNow(argdictCore):
        # configList
        configList: list = []

        # Configuration of `IBMQJobManager().run`
        # Multiple jobs shared
        shots: int = 1024
        backend: Backend = Aer.get_backend('qasm_simulator')
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
        listExpID: list = []
        listFile: list = []

        tagMapExpsID: TagMapExpsIDType = {
            'all': [], 'noTags': []}
        tagMapIndex: TagMapIndexType = {
            'all': [], 'noTags': []}
        tagMapQuantity: TagMapQuantityType = {
            'all': [], 'noTags': []}
        tagMapCounts: TagMapCountsType = {
            'all': [], 'noTags': []}

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

        ```
        {
            # configList
            'configList': [],

            # Configuration of `IBMQJobManager().run`
            # Multiple jobs shared
            'shots': 1024,
            'backend': Aer.get_backend('qasm_simulator'),
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
            Configuration: _description_
        """

        return Configuration(
            name=name,
            default={
                **self.argdictMultiNow()._asdict(),
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
        hintDefaults = {k: "" for k in self.expsConfig()}
        hintDefaults = {**hintDefaults, **hintContext}
        return hintDefaults

    """ Initialize """

    def initialize(self) -> dict[str: any]:
        """Configuration to Initialize Qurry.

        Returns:
            dict[str: any]: The basic configuration of `Qurry`.
        """

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

        # reresh per execution.
        self.now = argdict(
            params=self._expsConfig.make(),
        )
        self.IDNow = None
        self.multiNow = argdict(
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
    ) -> list[Optional[any]]:
        ...

    @overload
    def addWave(
        self,
        waveCircuit: QuantumCircuit,
        key=None,
    ) -> Optional[any]:
        ...

    def addWave(
        self,
        waveCircuit: Union[QuantumCircuit, list[QuantumCircuit]],
        key: Optional[Union[any, list[any]]] = None,
    ) -> Union[list[Optional[any]], Optional[any]]:
        """Add new wave function to measure.

        Args:
            waveCircuit (Union[QuantumCircuit, list[QuantumCircuit]]): The wave functions or circuits want to measure.
            key (Optional[any], optional): Given a specific key to add to the wave function or circuit,
                if `key == None`, then generate a number as key.
                Defaults to None.

        Returns:
            Optional[any]: Key of given wave function in `.waves`.
        """

        if isinstance(waveCircuit, QuantumCircuit):
            genKey = len(self.waves)
            if key == None:
                key = genKey

            if key in self.waves:
                while genKey in self.waves:
                    genKey += 1
                key = genKey
            else:
                ...

            self.lastWave = key
            self.waves[self.lastWave] = waveCircuit
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

    def waveInstruction(
        self,
        wave: Optional[any] = None,
        runBy: Optional[str] = 'gate',
        backend: Optional[Backend] = Aer.get_backend('qasm_simulator'),
    ) -> Union[Gate, Operator]:
        """Parse wave Circuit into `Instruction` as `Gate` or `Operator` on `QuantumCircuit`.

        Args:
            wave (Optional[any], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.
            runBy (Optional[str], optional):
                Export as `Gate` or `Operator`.
                Defaults to 'gate'.
            backend (Optional[Backend], optional):
                Current backend which to check whether exports to `IBMQBacked`,
                if does, then no matter what option input at `runBy` will export `Gate`.
                Defaults to Aer.get_backend('qasm_simulator').

        Returns:
            Union[Gate, Operator]: The result of the wave as `Gate` or `Operator`.
        """

        if wave == None:
            wave = self.lastWave

        if isinstance(backend, IBMQBackend):
            return self.waves[wave].to_gate()
        elif runBy == 'operator':
            return Operator(self.waves[wave])
        else:
            return self.waves[wave].to_gate()

    def waveOperator(
        self,
        wave: Optional[any] = None,
    ) -> Operator:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[any], optional):
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
        wave: Optional[any] = None,
    ) -> Gate:
        """Export wave function as `Gate`.

        Args:
            wave (Optional[any], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.

        Returns:
            Gate: The gate of wave function.
        """
        return self.waveInstruction(wave=wave)

    def find(
        self,
        expID: Optional[str] = None,
    ) -> str:
        """Check whether given `expID` is available,
        If does, then return it, otherwise return `False`.
        Or given current `expID` when doesn't give any id.

        Args:
            expID (Optional[str], optional): The `expID` wants to check. Defaults to None.

        Raises:
            KeyError: When given `expID` is not available.

        Returns:
            str: The available `expID`.
        """

        if expID != None:
            if expID in self.exps:
                tgtId = expID
            else:
                tgtId = False
        else:
            tgtId = self.IDNow

        return tgtId

    def drawWave(
        self,
        wave: Optional[any] = None,
        drawMethod: Optional[str] = 'text',
        decompose: Optional[int] = 1,
    ) -> Figure:
        """Draw the circuit of wave function.

        Args:
            wave (Optional[any], optional):
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

    def paramsControlMain(
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

    def paramsControlCore(
        self,
        # ID of experiment.
        expID: Optional[str] = None,
        # Qiskit argument of experiment.
        # Multiple jobs shared
        shots: int = 1024,
        backend: Backend = Aer.get_backend('qasm_simulator'),
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
        expsName: str = 'exps',
        tags: Optional[TagKeysAllowable] = None,

        **otherArgs: any,
    ) -> argdictNow:
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
            'backend': Aer.get_backend('qasm_simulator'),
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
                Defaults to `Aer.get_backend('qasm_simulator')`.

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

        # Export all arguments
        parsedOther = self.paramsControlMain(**otherArgs)
        self.now: self.argdictNow = argdict(
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
            wave (Optional[any], optional):
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

    def circuitMethod(self) -> list[QuantumCircuit]:
        """The method to construct circuit.
        Where should be overwritten by each construction of new measurement.

        Returns:
            Union[QuantumCircuit, list[QuantumCircuit]]:
                The quantum circuit of experiment.
        """
        argsNow: Qurry.argdictNow = self.now
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
        argsNow = self.paramsControlCore(**allArgs)

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
    ) -> dict[str: any]:
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
            k: self.exps[legacyId][k] for k in self.exps[legacyId] if k not in ['sideProduct']+excepts
        }

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
        filename: Optional[Union[Path, str]] = None,
        saveLocation: Union[Path, str] = Path('./'),
        expID: Optional[str] = None,
    ) -> dict[str: any]:
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
            dict[str: any]: The data.
        """

        if isinstance(saveLocation, (Path, str)):
            saveLocation = Path(saveLocation)
        else:
            raise ValueError(
                "'saveLocation' needs to be the type of 'str' or 'Path'.")

        if not os.path.exists(saveLocation):
            raise FileNotFoundError("Such location not found.")

        legacyRead = {}
        if expID != None:
            lsfolder = glob.glob(str(saveLocation / f"*{expID}*.json"))
            if len(lsfolder) == 0:
                raise FileNotFoundError(f"The file 'expID={expID}' not found.")

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
            {paramsControlArgsDoc}

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

        result = execution.result()
        self.exps[self.IDNow]['result'] = result

        return result

    def retrieve(
        self,
        **allArgs: any,
    ) -> Optional[list[dict]]:
        """Retrieve the data from IBMQService which is already done, and add it into `self.exps`.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.

        Raises:
            KeyError: The necessary keys in `self.now.dataRetrieve` are lost.
                When the job record does not have `jobID`.
            ValueError: `argsNow.dataRetrieve` is null.

        Returns:
            Optional[list[dict]]: The result of the job.
        """

        argsNow = self.paramsControlCore(**allArgs)
        if not isinstance(argsNow.provider, AccountProvider):
            raise ValueError("Provider required.")

        retrievedBase = self._expsBase.make()

        if isinstance(argsNow.dataRetrieve, dict):
            lost = self._expsBase.check(argsNow.dataRetrieve)
            for k in lost:
                if k in ["jobID", "IBMQJobManager"]:
                    raise KeyError(
                        f"The giving data to retrieve jobs needs the key '{k}'")
            retrievedBase = argsNow.dataRetrieve

        elif isinstance(argsNow.dataRetrieve, str):
            retrievedBase["jobID"] = [argsNow.dataRetrieve]

        else:
            raise ValueError(
                "The giving data to retrieve jobs has to be 'str' of 'jobID' or 'dict' contained 'jobID'.")

        result = None
        for singleJobID in retrievedBase["jobID"]:
            try:
                retrieved = IBMQJobManager().retrieve_job_set(
                    job_set_id=singleJobID,
                    provider=argsNow.provider,
                    refresh=True
                )
                result = retrieved.results()

            except IBMQJobManagerUnknownJobSet as e:
                warnings.warn("Job unknown.", e)

            except IBMQJobManagerInvalidStateError as e:
                warnings.warn(
                    "Job faied by 'IBMQJobManagerInvalidStateError'", e)

            except JobError as e:
                warnings.warn("Job faied by 'JobError", e)

        self.exps[self.IDNow] = {
            **self.exps[self.IDNow],
            'expID': self.IDNow,
            'result': result,
            **retrievedBase,
        }

        return result

    @abstractmethod
    def quantity(self) -> tuple[Quantity, Counts]:
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
        **otherArgs,
    ):
        """Computing specific squantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            tuple[dict, dict]:
                Counts, purity, entropy of experiment.
        """
        if resultIdxList == None:
            resultIdxList = [0]
        else:
            ...

        warnings.warn(
            "It's default '.quantity' which exports meaningless value.",
            UnconfiguredWarning)
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
        **allArgs: any,
    ) -> Union[Quantity, tuple[Quantity, Counts]]:
        """Export the result which completed calculating purity.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.

        Returns:
            dict[float]: The result.
        """
        print(f"+"+"-"*20+"\n"+f"| Calculating {self.__name__}...")

        result = (self.retrieve if dataRetrieve != None else self.run)(
            dataRetrieve=dataRetrieve,
            **allArgs,
        )
        argsNow = self.now
        print(f"| name: {self.now.expsName}\n"+f"| id: {self.IDNow}")

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

    def paramsControlMulti(
        self,
        # configList
        configList: list = [],
        # Configuration of `IBMQJobManager().run`
        # Multiple jobs shared
        shots: int = 1024,
        backend: Backend = Aer.get_backend('qasm_simulator'),
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
    ) -> argdictMultiNow:
        """Handling all arguments and initializing a single experiment.

        - example of a value in `self.exps`

        ```
        {
            # configList
            'configList': [],

            # Configuration of `IBMQJobManager().run`
            # Multiple jobs shared
            'shots': 1024,
            'backend': Aer.get_backend('qasm_simulator'),
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
                Defaults to `Aer.get_backend('qasm_simulator')`.

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
            argdict: Current arguments.
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

        self.multiNow: self.argdictMultiNow = argdict(
            params={
                **self._expsMultiConfig.make(),
                **otherArgs,
                # configList
                'configList': initedConfigList,

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

                # `writeLegacy`
                'additionName': additionName,
                'saveLocation': Path(saveLocation),
                'exportLocation': exportLocation,

                'gitignore': gitignore,
                'listExpID': [],  # expIDList
                'listFile': [],  # fileList
                # 'listQuantity': [],  # expPurityList/expEntropyList
                'tagMapExpsID': {
                    'all': [], 'noTags': []},  # expsBelong
                'tagMapIndex': {
                    'all': [], 'noTags': []},
                'tagMapQuantity': {
                    'all': [], 'noTags': []},
                'tagMapCounts': {
                    'all': [], 'noTags': []},

                'circuitsMap': {},
                'circuitsNum': {},

                'type': jobsType,
                'state': 'init',
            },
            paramsKey=self._expsMultiConfig.make().keys(),
        )

        return self.multiNow

    @staticmethod
    def _legacyTagGuider(
        field: dict,
        legacyTag: any,
        v: any,
    ) -> dict:
        """_summary_

        Args:
            field (dict): _description_
            legacyTag (any): _description_
            v (any): _description_

        Returns:
            dict: _description_
        """

        fieldCopy = {**field}
        if legacyTag == None:
            fieldCopy['noTags'].append(v)
        elif legacyTag in fieldCopy:
            fieldCopy[legacyTag].append(v)
        else:
            fieldCopy[legacyTag] = [v]

        return fieldCopy

    def multiOutput(
        self,
        configList: list = [],
        shots: int = 1024,
        backend: Backend = Aer.get_backend('qasm_simulator'),

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
                Defaults to `Aer.get_backend('qasm_simulator')`.

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
            quantity, counts = self.output(**config, withCounts=True)

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

            # packing
            argsMulti['listFile'].append(legacy['filename'])
            argsMulti['listExpID'].append(self.IDNow)

            argsMulti.tagMapExpsID = self._legacyTagGuider(
                argsMulti.tagMapExpsID, legacyTag, self.IDNow
            )
            argsMulti.tagMapIndex = self._legacyTagGuider(
                argsMulti.tagMapIndex, legacyTag, config['expIndex']
            )
            argsMulti.tagMapIndex = self._legacyTagGuider(
                argsMulti.tagMapIndex, 'all', config['expIndex']
            )

            argsMulti.tagMapQuantity = self._legacyTagGuider(
                argsMulti.tagMapQuantity, 'all', quantity
            )
            argsMulti.tagMapQuantity = self._legacyTagGuider(
                argsMulti.tagMapQuantity, legacyTag, quantity
            )

            argsMulti.tagMapCounts = self._legacyTagGuider(
                argsMulti.tagMapCounts, 'all', counts
            )
            argsMulti.tagMapCounts = self._legacyTagGuider(
                argsMulti.tagMapCounts, legacyTag, counts
            )

        print(f"| Export...")
        argsMulti['gitignore'].ignore('*.json')
        argsMulti.state = 'completed'
        dataMultiJobs = argsMulti.jsonize()

        for n, data in [
            ('multiJobs.json', dataMultiJobs),
            ('tagMapQuantity.json', argsMulti['tagMapQuantity']),
            ('tagMapCounts.json', argsMulti['tagMapCounts']),
        ]:
            argsMulti['gitignore'].sync(f'*.{n}')
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
                argsMulti['gitignore'].sync(f'*.{n}.json')
                print(f"| Export {n}.json")
                quickJSONExport(
                    content=argsMulti[n],
                    filename=argsMulti.exportLocation /
                    f"{argsMulti.expsName}.{n}.json",
                    mode='w+',
                    jsonablize=True)

        argsMulti['gitignore'].export(argsMulti.exportLocation)
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

        for n in [
            'tagMapExpsID',
            'tagMapIndex',
            'tagMapQuantity',
            'tagMapCounts',
        ]:
            if n in dataDummyJobs:
                dataDummyJobs[n] = keyTupleLoads(dataDummyJobs[n])

        gc.collect()
        print(
            f"| MultiRead {self.__name__} End in {time.time() - start_time} sec ...\n"+f"+"+"-"*20)

        return dataDummyJobs

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
            argsMulti['circuitsNum'][self.IDNow] = numCirc

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

            argsMulti['listFile'].append(legacy['filename'])
            argsMulti['listExpID'].append(self.IDNow)

            argsMulti.tagMapExpsID = self._legacyTagGuider(
                argsMulti.tagMapExpsID, legacyTag, self.IDNow
            )
            argsMulti.tagMapIndex = self._legacyTagGuider(
                argsMulti.tagMapIndex, legacyTag, config['expIndex']
            )
            argsMulti.tagMapIndex = self._legacyTagGuider(
                argsMulti.tagMapIndex, 'all', config['expIndex']
            )

        with Gajima(
            enumerate(argsMulti['listExpID']),
            carousel=[('dots', 20, 6), 'basic'],
            prefix="| ",
            desc="Packing circuits for pending",
            finish_desc="Packing Completed",
        ) as gajima:
            for expIndex, expIDKey in gajima:
                argsMulti['circuitsMap'][expIDKey] = []
                tmpCircuitNum = argsMulti['circuitsNum'][expIDKey]
                gajima.gprint(
                    f"| Packing expID: {expIDKey}, index={expIndex} with {tmpCircuitNum} circuits ...")

                for i in range(tmpCircuitNum):
                    argsMulti['circuitsMap'][expIDKey].append(
                        len(pendingArray))
                    if not isinstance(allTranspliedCircs[expIDKey][i], QuantumCircuit):
                        print(allTranspliedCircs[expIDKey][i], i)
                        raise ValueError("Critical Error")
                    pendingArray.append(allTranspliedCircs[expIDKey][i])

        with Gajima(
            carousel=[('dots', 20, 6), 'basic'],
            prefix="| ",
            desc="Pending Jobs",
            finish_desc="Pending end and Exporting",
        ) as gajima:
            JobManager = IBMQJobManager()
            powerJob = JobManager.run(
                **argsMulti.managerRunArgs,
                experiments=pendingArray,
                backend=argsMulti.backend,
                shots=argsMulti.shots,
                name=f'{argsMulti.expsName}_w/_{len(pendingArray)}_jobs',
                # job_tags=argsMulti.pendingTags
                # ? waiting for the issue of contain
            )
            print(f"| report:", JobManager.report())
            powerJobID = powerJob.job_set_id()
            gajima.gprint(f"| name: {powerJob.name()}")
            argsMulti.powerJobID = powerJobID
            # powerJobsIDList = [mj.job.job_id() for mj in powerJob.jobs()]

        argsMulti['gitignore'].ignore('*.json')
        dataPowerJobs = argsMulti.jsonize()
        argsMulti.state = 'pending'

        argsMulti['gitignore'].sync(f'*.powerJobs.json')
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
                argsMulti['gitignore'].sync(f'*.{n}.json')
                print(f"| Export {n}.json")
                quickJSONExport(
                    content=argsMulti,
                    filename=argsMulti.exportLocation /
                    f"{argsMulti.expsName}.{n}.json",
                    mode='w+',
                    jsonablize=True)

        argsMulti['gitignore'].export(argsMulti.exportLocation)

        gc.collect()
        print(
            f"| PowerPending {self.__name__} End in {round(time.time() - start_time, 2)} sec ...\n" +
            f"+"+"-"*20)

        return dataPowerJobs

    def powerOutput(
        self,
        exportName: Union[Path, str],
        saveLocation: Union[Path, str] = './',
        dataRetrieve: bool = False,
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
            saveLocation=saveLocation,
            **allArgs,
        )
        argsMulti: self.argdictMultiNow = self.multiNow

        print(f"| PowerOutput {self.__name__} Start...\n"+f"+"+"-"*20)
        if dataPowerJobs['type'] == 'multiJobs':
            print(
                f"| PowerOutput {self.__name__} End " +
                "with reading a multiJobs in {time.time() - start_time} sec ...\n" +
                f"+"+"-"*20)
            return dataPowerJobs

        if dataPowerJobs['state'] == 'pending':
            print(f"| Retrieve result...")
            powerJob = IBMQJobManager().retrieve_job_set(
                job_set_id=dataPowerJobs['powerJobID'],
                provider=argsMulti.provider,
            )

        elif overwrite and isinstance(overwrite, bool):
            print(f"| Overwrite activate and retrieve result...")
            powerJob = IBMQJobManager().retrieve_job_set(
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
                saveLocation=Path(dataPowerJobs['exportLocation']),
            )

            counts, quantity = self.quantity(**{
                **self.exps[expIDKey],
                'result': powerResult,
                'resultIdxList': dataPowerJobs['circuitsMap'][expIDKey],
            })
            self.exps[expIDKey] = {
                **self.exps[expIDKey],
                **quantity,
                'counts': counts,
            }

            # legacy writer
            legacy = self.writeLegacy(
                saveLocation=Path(dataPowerJobs['exportLocation']),
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

            dataPowerJobs['tagMapQuantity'] = self._legacyTagGuider(
                dataPowerJobs['tagMapQuantity'], 'all', quantity
            )
            dataPowerJobs['tagMapQuantity'] = self._legacyTagGuider(
                dataPowerJobs['tagMapQuantity'], legacyTag, quantity
            )

            dataPowerJobs['tagMapCounts'] = self._legacyTagGuider(
                dataPowerJobs['tagMapCounts'], 'all', counts
            )
            dataPowerJobs['tagMapCounts'] = self._legacyTagGuider(
                dataPowerJobs['tagMapCounts'], legacyTag, counts
            )

            print(f"| index={idxNum} end...\n"+f"+"+"-"*20)
            idxNum += 1

        print(f"| Export...")
        argsMulti['gitignore'].ignore('*.json')
        dataPowerJobs['state'] = 'completed'
        dataPowerJobs = jsonablize(dataPowerJobs)

        for n, data in [
            ('powerJobs.json', dataPowerJobs),
            ('tagMapQuantity.json', dataPowerJobs['tagMapQuantity']),
            ('tagMapCounts.json', dataPowerJobs['tagMapCounts']),
        ]:
            argsMulti['gitignore'].sync(f'*.{n}')
            print(f"| Export {n}")
            quickJSONExport(
                content=data,
                filename=Path(dataPowerJobs['exportLocation']) /
                f"{dataPowerJobs['expsName']}.{n}",
                mode='w+',
                jsonablize=True)

        if argsMulti.independentExports:
            print(f"| independentExports...")
            for n in [
                'tagMapQuantity',
                'tagMapIndex'
            ]:
                argsMulti['gitignore'].sync(f'*.{n}.json')
                print(f"| Export {n}.json")
                quickJSONExport(
                    content=dataPowerJobs[n],
                    filename=Path(dataPowerJobs['exportLocation']) /
                    f"{dataPowerJobs['expsName']}.{n}.json",
                    mode='w+',
                    jsonablize=True)

        argsMulti['gitignore'].export(Path(dataPowerJobs['exportLocation']))
        gc.collect()
        print(
            f"| PowerOutput {self.__name__} End in {round(time.time() - start_time, 2)} sec ...\n"+f"+"+"-"*20)

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
