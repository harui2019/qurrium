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
import time

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
            # ID of experiment.
            'expID': None,

            # Variants of experiment.
            **defaultArg,

            # Qiskit argument of experiment.
            # Multiple jobs shared
            'shots': 1024,
            'backend': Aer.get_backend('qasm_simulator'),
            'provider': None,
            'runConfig': {},

            'expsName': None,

            # Single job dedicated
            'runBy': "gate",
            'decompose': 1,
            'transpileArgs': {},

            # Other arguments of experiment
            'drawMethod': 'text',
            'resultKeep': False,
            'dataRetrieve': None,
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
        'jobID': [],
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
        'dataRetrieve': False,
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
            'dataRetrieve': False,
            'expsName': 'exps',

            # Multiple job dedicated
            'independentExports': False,

            # `writeLegacy`
            'additionName': 'export',
            'saveLocation': Path('./'),
            'exportLocation': None,
        },
    )


def expsHint(
    name: str = 'qurryBaseHint',
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

        return {
            'wave': wave,
            'expsName': f"{expsName}-dummy.{wave}",
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
        tags: Optional[dataTagsAllow] = None,

        **otherArgs: any,
    ) -> argdict:
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
            'jobID': [],
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
        self.now = argdict(
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
            Union[QuantumCircuit,list[QuantumCircuit]]] = None,
        whichCircuit: Optional[int] = 0,
        drawMethod: Optional[str] = 'text',
        decompose: Optional[int] = 0,
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
        numQubits = self.waves[self.now.wave].num_qubits

        q1 = QuantumRegister(numQubits, 'q1')
        c1 = ClassicalRegister(numQubits, 'c1')
        circuit = QuantumCircuit(q1, c1)

        circuit.h(0)
        # circuit.append(
        #     self.waveInstruction(
        #         wave=self.now.wave,
        #         runBy=self.now.runBy,
        #         backend=self.now.backend,
        #     ),
        #     [circuit[i] for i in range(numQubits)],
        # )
        for i in range(numQubits):
            circuit.measure(q1[i], c1[i])
        print("It's default circuit, the quantum circuit is not yet configured.")

        return [circuit]

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
    ) -> dict[str: any]:
        """Export the experiment data, if there is a previous export, then will overwrite.

        - example of file.name:

            `{name}.{self.exps[expID]['expsName']}.expId={expID}.json`

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
        if not legacyId:
            warnings.warn(
                f"No such expID '{expID}', waiting for legacy be written.")
            return {}

        filename = (
            Path(
                f"{additionName}.{self.exps[legacyId]['expsName']}.expId={legacyId}.json")
        ) if additionName else (
            Path(f"{self.exps[legacyId]['expsName']}.expId={legacyId}.json")
        )
        self.exps[legacyId]['filename'] = filename

        if isinstance(saveLocation, (Path, str)):
            saveLocParts = Path(saveLocation).parts
            saveLoc = Path(saveLocParts[0]) if len(
                saveLocParts) > 0 else Path('./')
            for p in saveLocParts[1:]:
                saveLoc /= p

            if not os.path.exists(saveLoc):
                os.mkdir(saveLoc)

            self.exps[legacyId]['saveLocation'] = saveLoc
            legacyExport = jsonablize(self.exps[legacyId])
            with open((saveLoc / filename), 'w+', encoding='utf-8') as Legacy:
                json.dump(legacyExport, Legacy, indent=2, ensure_ascii=False)

        elif saveLocation == None:
            legacyExport = jsonablize(self.exps[legacyId])

        else:
            legacyExport = jsonablize(self.exps[legacyId])
            warnings.warn(
                "'saveLocation' is not the type of 'str' or 'Path', " +
                "so export cancelled.")

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
                When the job record does not have `jobId`.
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
                result = retrieved.results().combine_results()

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

    @classmethod
    def quantity(
        cls,
        shots: int,
        result: Union[Result, ManagedResults],
        resultIdxList: Optional[list[int]] = None,
        **otherArgs,
    ) -> tuple[dict, dict]:
        """Computing specific quantity.
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
            "It's default '.quantity' which exports meaningless value.")
        counts = result.get_counts(resultIdxList[0])

        dummy = -100
        quantity = {
            '_dummy': dummy,
            'echo': '_dummy_value',
        }
        return counts, quantity

    def output(
        self,
        dataRetrieve: Optional[dict[Union[list[str], str]]] = None,
        **allArgs: any,
    ) -> dict[float]:
        """Export the result which completed calculating purity.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.

        Returns:
            dict[float]: The result.
        """

        result = (self.retrieve if dataRetrieve != None else self.run)(
            dataRetrieve=dataRetrieve,
            **allArgs,
        )
        argsNow = self.now

        print(
            f"| Calculating {self.__name__}...\n" +
            f"| name: {self.now.expsName}, id: {self.IDNow}"
        )

        counts, quantity = self.quantity(
            **argsNow,
            result=result,
        )

        if argsNow.resultKeep:
            warnings.warn(
                "Result will keep, but it may cause memory overallocated.")
            self.exps[self.IDNow]['result'] = result

        else:
            print("Entropy and Purity are figured out, result will clear.")
            del self.exps[self.IDNow]['result']

        self.exps[self.IDNow] = {
            **self.exps[self.IDNow],
            **quantity,
            'counts': counts,

        }
        gc.collect()
        print(f"| End...\n"+f"+"+"-"*20)

        return quantity
    
    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        expsName: str = 'exps',
        **otherArgs: any
    ) -> dict:
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
        return self.output(
            wave=wave,
            expsName=expsName,
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
        dataRetrieve: Optional[Union[dict[any], bool]] = None,
        expsName: str = 'exps',
        independentExports: bool = False,
        # `writeLegacy`
        additionName: Optional[str] = None,
        saveLocation: Union[Path, str] = Path('./'),

        **otherArgs: any,
    ) -> argdict:
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
            'dataRetrieve': False,
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
            # ID of experiment.

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
            dataRetrieve (Optional[Union[dict[any], bool]], optional):
                Data to collect results from IBMQ via `IBMQJobManager`.
                Defaults to `None`.

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
        if dataRetrieve:
            immutableName = expsName
            exportLocation = Path(saveLocation) / immutableName
            print(
                f"| Retrieve {immutableName}...\n" +
                f"| at: {exportLocation}"
            )

        else:
            rjustLen = 3 if int(np.log10(indexRename))+2 <= 3 else int(np.log10(indexRename))+2
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
        expIndex = 0
        initedConfigList = []
        for config in configList:
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
            expIndex += 1

        # dataRetrieve
        powerJobID = None
        if isinstance(dataRetrieve, str):
            powerJobID = dataRetrieve
        elif isinstance(dataRetrieve, dict):
            ...

        # gitignore
        gitignore = syncControl()

        self.multiNow = argdict(
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
                'dataRetrieve': dataRetrieve,
                'expsName': immutableName,

                # Multiple job dedicated
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
                'tagMapQuantity': {
                    'all': [], 'noTags': []},
                'tagMapIndex': {
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
        **allArgs: any,
    ) -> dict[any]:
        """Make multiple jobs output.

        Args:
            allArgs: all arguments will handle by `.paramsControlMulti()` and export as specific format.

        Returns:
            dict[any]: All result of jobs.
        """
        start_time = time.time()
        argsMulti = self.paramsControlMulti(
            configList=configList,
            **allArgs
        )

        print(f"| MultiOutput {self.__name__} Start...\n"+f"+"+"-"*20)
        for config in argsMulti.configList:
            print(f"| index={config['expIndex']} start...")
            quantity = self.output(**config)

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

            argsMulti.tagMapQuantity = self._legacyTagGuider(
                argsMulti.tagMapQuantity, 'all', quantity
            )
            argsMulti.tagMapQuantity = self._legacyTagGuider(
                argsMulti.tagMapQuantity, legacyTag, quantity
            )
            print(f"| index={config['expIndex']} end...\n"+f"+"+"-"*20)

        print(f"| Export...")
        argsMulti['gitignore'].ignore('*.json')
        argsMulti.state = 'completed'
        dataMultiJobs = argsMulti.jsonize()

        for n, data in [
            ('multiJobs.json', dataMultiJobs),
            ('tagMapQuantity.json', argsMulti['tagMapQuantity']),
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
                'tagMapQuantity',
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
            f"| MultiOutput {self.__name__} End in {time.time() - start_time} sec ...\n"+f"+"+"-"*20)

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
        argsMulti = self.paramsControlMulti(
            saveLocation=saveLocation,
            expsName=exportName,
            dataRetrieve=True,
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
                'tagMapQuantity',
                'tagMapIndex',
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
            'tagMapQuantity',
            'tagMapIndex',
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
        for config in argsMulti.configList:
            print(f"| index={config['expIndex']} start...")
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
            print(f"| index={config['expIndex']} end...\n"+f"+"+"-"*20)

        print(f"| Preparing jobs pending ...")
        argsMulti['gitignore'].ignore('*.json')

        expIndex = 0
        for expIDKey in argsMulti['listExpID']:
            argsMulti['circuitsMap'][expIDKey] = []
            tmpCircuitNum = argsMulti['circuitsNum'][expIDKey]
            print(
                f"| Packing expID: {expIDKey}, index={expIndex} with {tmpCircuitNum} circuits ...")

            for i in range(tmpCircuitNum):
                argsMulti['circuitsMap'][expIDKey].append(len(pendingArray))
                pendingArray.append(allTranspliedCircs[expIDKey][i])
            expIndex += 1

        print(
            f"| Preparing end...\n"+f"+"+"-"*20 +
            f"| .powerJobs.json export without JobID ...")

        dataPowerJobs = argsMulti.jsonize()
        argsMulti.state = 'pending'
        argsMulti['gitignore'].sync(f'*.powerJobs.json')
        quickJSONExport(
            content=dataPowerJobs,
            filename=argsMulti.exportLocation /
            f"{argsMulti.expsName}.powerJobs.json",
            mode='w+',
            jsonablize=True)

        print(f"| Pending Jobs ...")
        powerJob = IBMQJobManager().run(
            **argsMulti.managerRunArgs,
            experiments=pendingArray,
            backend=argsMulti.backend,
            shots=argsMulti.shots,
            name=f'{argsMulti.expsName}_w/_{len(pendingArray)}_jobs',
        )
        powerJobID = powerJob.job_set_id()
        argsMulti.powerJobID = powerJobID
        print(
            f"| Pending end...\n"+f"+"+"-"*20 +
            f"| Export ...")

        dataPowerJobs = argsMulti.jsonize()
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
            f"| PowerPending {self.__name__} End in {time.time() - start_time} sec ...\n"+f"+"+"-"*20)

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
        argsMulti = self.multiNow

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
        powerResultRaw: ManagedResults = powerJob.results()
        powerResult: Result = powerResultRaw.combine_results()
        
        idxNum = 0
        for expIDKey in dataPowerJobs['listExpID']:
            print(f"| index={idxNum} start...")
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
            print(f"| index={idxNum} end...\n"+f"+"+"-"*20)
            idxNum += 1
            
        print(f"| Export...")
        argsMulti['gitignore'].ignore('*.json')
        dataPowerJobs['state'] = 'completed'
        dataPowerJobs = jsonablize(dataPowerJobs)
                
        for n, data in [
            ('powerJobs.json', dataPowerJobs),
            ('tagMapQuantity.json', dataPowerJobs['tagMapQuantity']),
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
            f"| PowerOutput {self.__name__} End in {time.time() - start_time} sec ...\n"+f"+"+"-"*20)

        return dataPowerJobs

    """Other"""

    def reset(
        self,
        *args,
        security: bool = False,
    ) -> None:
        """Reset the measurement and release memory.

        Args:
            security (bool, optional): Security for reset. Defaults to False.
        """

        if security and isinstance(security, bool):
            self.__init__(self.waves)
            gc.collect()
            warnings.warn(
                "The measurement has reset and release memory allocating.")
        else:
            warnings.warn(
                "Reset does not execute to prevent reset accidentally, " +
                "if you are sure to do it, then use '.reset(security=True)'."
            )

    def __repr__(self) -> str:
        return f"<{self.__name__}({len(self.exps)} experiments made)>"

    def to_dict(self) -> dict:
        return self.__dict__
