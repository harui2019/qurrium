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
    keyTupleLoads
)
# Qurry V0.3.1 - a Qiskit Macro


def defaultCircuit(numQubit: int) -> QuantumCircuit:
    return QuantumCircuit(numQubit)


def expsConfig(
    name: str = 'qurryConfig',
    defaultArg: dict[any] = {
        # Variants of experiment.
        'wave': None,
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
        ## Multiple jobs shared 
        'shots': 1024,
        'backend': Aer.get_backend('qasm_simulator'),
        'runConfig': {}

        ## Single job dedicated
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
            # ID of experiment.
            'expID': None,

            # Variants of experiment.
            **defaultArg,

            # Qiskit argument of experiment.
            # Multiple jobs shared
            'shots': 1024,
            'backend': Aer.get_backend('qasm_simulator'),
            'runConfig': {},

            # Single job dedicated
            'runBy': "gate",
            'decompose': 1,
            'transpileArgs': {},

            # Other arguments of experiment
            'drawMethod': 'text',
            'resultKeep': False,
            'dataRetrieve': None,
            'expsName': None,
            'tag': None,
        },
    )


def expsBase(
    name: str = 'qurryExpsBase',
    expsConfig: dict = expsConfig(),
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
        ## Multiple jobs shared 
        'shots': 1024,
        'backend': Aer.get_backend('qasm_simulator'),
        'runConfig': {}

        ## Single job dedicated
        'runBy': "gate",
        'decompose': 1,
        'transpileArgs': {},

        # Other arguments of experiment
        'drawMethod': 'text',
        'resultKeep': False,
        'dataRetrieve': None,

        # Reault of experiment.
        'echo': -100,

        # Measurement result
        'circuit': None,
        'figRaw': 'unexport',
        'figTranspile': 'unexport',
        'result': None,
        'counts': None,

        # Export data
        'jobID': [],
        'expsName': 'exps',
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
            **expsConfig,

            # Reault of experiment.
            **defaultArg,

            # Measurement result
            'circuit': None,
            'figRaw': 'unexport',
            'figTranspile': 'unexport',
            'result': None,
            'counts': None,

            # Export data
            'jobID': [],
            'expsName': 'exps',
        },
    )


def expsConfigMulti(
    name: str = 'qurryConfigMulti',
    expsConfig: dict = expsConfig(),
    defaultArg: dict[any] = {
        # Variants of experiment.
    },
) -> Configuration:
    """The default format and value for executing mutiple experiments.
    - Example:

    ```
    {
        'configList': [ ...expsConfigs ], 

        # Configuration of `IBMQJobManager().run`
        'shots': 1024,
        'backend': Aer.get_backend('qasm_simulator'),
        'name': None,
        'maxExperimentsPerJob' None,
        'runConfig': {},
        'managerRunArgs': {},
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
            'configList': [],

            # Configuration of `IBMQJobManager().run`
            'shots': 1024,
            'backend': Aer.get_backend('qasm_simulator'),
            'name': None,
            'maxExperimentsPerJob': None,
            'runConfig': {},
            'managerRunArgs': {},
        },
    )


def expsHint(
    name: str = 'qurryExpsBase',
    expsConfig: dict = expsBase(),
    hintContext: dict = {
        "_basicHint": "This is a hint of qurry.",
    },
) -> dict:
    hintDefaults = {k: "" for k in expsConfig}
    hintDefaults = {**hintDefaults, **hintContext}
    return hintDefaults


dataTagAllow = Union[str, int, float, bool]
dataTagsAllow = Union[tuple[dataTagAllow], dataTagAllow]


_expsConfig = expsConfig()
_expsBase = expsBase()
_expsMultiConfig = expsConfigMulti()
_expsHint = expsHint()


class Qurry:
    """Qurry V0.3.1
    The qiskit job tool
    """

    """ Initialize """

    def initialize(self) -> dict[str: any]:
        """Configuration to Initialize Qurry.

        Returns:
            dict[str: any]: The basic configuration of `Qurry`.
        """

        self._expsConfig = _expsConfig
        self._expsBase = _expsBase
        self._expsHint = _expsHint
        self._expsMultiConfig = _expsMultiConfig
        self.shortName = 'qurry'

        return self._expsConfig, self._expsBase,

    def __init__(
        self,
        waves: Union[QuantumCircuit, list[QuantumCircuit]] = defaultCircuit,
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

        # basic check
        if hasattr(self, 'initialize'):
            for k in ['_expsConfig', '_expsBase', '_expsHint', 'shortName']:
                if not hasattr(self, k):
                    raise AttributeError(
                        f"'{k}' is lost, initialization stop.")

        # value create
        self.exps = {}
        self.expsBelong = {}

        # reresh per execution.
        self.now = argdict(
            params=self._expsConfig,
        )
        self.IDNow = None
        self.multiNow = argdict(
            params=self._expsMultiConfig,
        )

    """Wave Function"""
    @staticmethod
    def circuitDecomposer(
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

    def addWave(
        self,
        waveCircuit: QuantumCircuit,
        key: Optional[any] = None,
    ) -> Optional[any]:
        """Add new wave function to measure.

        Args:
            waveCircuit (QuantumCircuit): The wave functions or circuits want to measure.
            key (Optional[any], optional): Given a specific key to add to the wave function or circuit, 
                if `key == None`, then generate a number as key. 
                Defaults to None.

        Returns:
            Optional[any]: Key of given wave function in `.waves`.
        """

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
        if isinstance(waveCircuit, QuantumCircuit):
            self.waves[self.lastWave] = waveCircuit
            return self.lastWave
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

    def drawWave(
        self,
        wave: Optional[any] = None,
        drawMethod: Optional[str] = 'text',
        decompose: Optional[int] = 1,
    ) -> Union[str, Figure]:
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

        qcDummy = self.circuitDecomposer(qcDummy, decompose)

        fig = qcDummy.draw(drawMethod)

        return fig

    def paramsControlMain(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
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

            otherArgs (any):
                Other arguments.

        Returns:
            dict: The export will be processed in `.paramsControlCore`
        """

        # wave
        if isinstance(wave, QuantumCircuit):
            wave = self.addWave(wave)
            print(f"Add new wave with key: {wave}")
        elif wave == None:
            wave = self.lastWave
            print(f"Autofill will use '.lastWave' as key")
        else:
            try:
                self.waves[wave]
            except KeyError as e:
                warnings.warn(f"'{e}', use '.lastWave' as key")
                wave = self.lastWave

        return {
            'wave': wave,
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
        tag: Optional[Union[tuple[str], str]] = None,

        **otherArgs: any,
    ) -> argdict:
        """Handling all arguments and initializing a single experiment.

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

            expsName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            tag (Optional[Union[list[any], any]], optional):
                Given the experiment multiple tag to make a dictionary for recongnizing it.
                Defaults to `None`.

            otherArgs (any):
                Other arguments includes the variants of experiment.

        Raises:
            KeyError: Given `expID` does not exist.

        Returns:
            tuple[str, dict[str: any]]: Current `expID` and arguments.
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

        # tag
        if tag in self.expsBelong:
            self.expsBelong[tag].append(self.IDNow)
        else:
            self.expsBelong[tag] = [self.IDNow]

        # Export all arguments
        parsedOther = self.paramsControlMain(**otherArgs)
        self.now = argdict(
            params={
                **self._expsBase,
                'expID': self.IDNow,

                'shots': shots,
                'backend': backend,
                'provider': provider,
                'runConfig': runConfig,

                'runBy': 'gate' if isinstance(backend, IBMQBackend) else runBy,
                'decompose': decompose,
                'transpileArgs': transpileArgs,

                'drawMethod': drawMethod,
                'resultKeep': resultKeep,
                'dataRetrieve': dataRetrieve,
                'expsName': expsName,
                'tag': tag,

                **parsedOther,
            },
            paramsKey=self._expsBase.keys(),
        )

        return self.now
