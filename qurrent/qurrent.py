from __future__ import annotations
from re import S
from pyrsistent import immutable

from qiskit import (
    Aer, execute, transpile,
    QuantumRegister, ClassicalRegister, QuantumCircuit)
from qiskit.tools import *
from qiskit.visualization import *

from qiskit.providers import Backend, BaseJob, JobError
from qiskit.providers.ibmq import IBMQBackend
from qiskit.providers.ibmq.managed import (
    IBMQJobManager, ManagedJobSet, ManagedResults,
    IBMQJobManagerInvalidStateError, IBMQJobManagerUnknownJobSet)
from qiskit.providers.ibmq.accountprovider import AccountProvider

from qiskit.quantum_info import Operator
from qiskit.circuit.gate import Gate
from qiskit.result import Result

from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from math import pi
from uuid import uuid4
from pathlib import Path
import glob
import json
import gc
import warnings
from typing import Union, Optional, Annotated, Callable

from torch import NoneType

from ..tool import (
    Configuration, argdict,
    jsonablize, quickJSONExport, keyTupleLoads,
    syncControl, overNested,
)
# EntropyMeasureV2.1


defaultCircuit = QuantumCircuit(1)

qurrentConfig = Configuration(
    name="qurrentConfig",
    default={
        'wave': None,
        'expID': None,

        'params': None,
        'shots': 1024,

        'runBy': "gate",
        'backend': Aer.get_backend('qasm_simulator'),
        'drawMethod': 'text',
        'decompose': 1,
        'resultKeep': False,
        'dataRetrieve': None,
    },
)

measureBase = Configuration(
    name="measureBase",
    default={
        'circuit': None,
        'fig': 'unexport',
        'result': None,
        'counts': None,
        'purity': None,
        'entropy': None,

        'jobID': [],
        'IBMQJobManager': False,
        'name': 'unname',

        'aNum': None,
        'paramsOther': {},
        'wave': None,
        'expID': None,

        'params': None,
        'runBy': "gate",
        'shots': 1024,
        'backend': Aer.get_backend('qasm_simulator'),
        'drawMethod': 'text',
        'decompose': 1,
        'resultKeep': False,
        'dataRetrieve': None,
        'expsName': 'exps',
    },
)

neccessaryKey = [
    'filename',
    'aNum',
    'paramsOther',
    'wave',
    'expID',
    'params',
    'shots',
    'backend',
    'expsName',
]

MeasureConfig = Annotated[
    dict,
    """
    ```
    self.measureConfig = {
        'name': 'EntropyMeasureV2.1
        ',
        'paramsNum': 1,
        'default': {
            'degree': (half of the numbers of qubits of Wave Circuit.)
            # example: 8 -> 8/2 = 4,
            # example: 9 -> ((9-1)/2)+1 = 5
        },
        'hint': {
            'degree': 'degree of freedom of subsystem A.',
            'unConfig': '(This class is not yet configured.)',
        },
        'otherHint': (you can use this hint for other description.)
    }
    ```
    """
]

expsItem = Annotated[
    dict,
    """The record of single experiment.
    """
]

dataTagAllow = Union[str, int, float, bool]
dataTagsAllow = Union[tuple[dataTagAllow], dataTagAllow]

class EntropyMeasureV2:
    """EntropyMeasureV2.1 of qurrent
    """

    # Initialize
    def initialize(self) -> dict[str: any]:
        """Configuration to Initialize EntropyMeasure.
        It requires the following parameters are setted:
        ```
        self.measureConfig = {
            'name': 'EntropyMeasureV2.1',
            'shortName': 'qurrentV2.1', # the short name will be used for some export file naming.
            'paramsNum': 1,
            'default': {
                'degree': (half of the numbers of qubits of Wave Circuit.)
                # example: 8 -> 8/2 = 4,
                # example: 9 -> ((9-1)/2)+1 = 5
            },
            'hint': {
                'degree': 'degree of freedom of subsystem A.',
                'unConfig': '(This class is not yet configured.)',
            },
            'otherHint': (you can use this hint for other description.)
        }
        ```

        When you completed 'hint', then remove the key 'unConfig' to finish it.

        Returns:
            dict[str: any]: The basic configuration of `EntropyMeasureV2`.
        """

        self.measureConfig: MeasureConfig = {
            'name': 'EntropyMeasureV2.1',
            'shortName': 'qurrentV2.1',
            'paramsNum': 1,
            'default': {
                'degree': (
                    self.waves[self.lastWave].num_qubits/2 if (self.waves[self.lastWave].num_qubits % 2 == 0)
                    else int((self.waves[self.lastWave].num_qubits-1)/2+1))
            },
            'hint': {
                'degree': 'degree of freedom of subsystem A.',
                'unConfig': '(This class is not yet configured.)',
            },
            'otherHint': """ """,
        }
        self.paramsKey = []
        """Configuration paramsKey """

        return self.measureConfig

    def __init__(
        self,
        waves: Union[QuantumCircuit, list[QuantumCircuit]] = defaultCircuit,
    ) -> None:
        """The initialization of EntropyMeasure.

        Args:
            waves (Union[QuantumCircuit, list[QuantumCircuit]], optional): [description]. Defaults to defaultCircuit.

        Raises:
            ValueError: When input is a null list.
            TypeError: When input is nor a `QuantumCircuit` or `list[QuantumCircuit]`.
            KeyError: Configuration lost.
            KeyError: `self.measureConfig['hint']` is not completed.
        """

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
        measureConfig = self.initialize()
        for k in ['name', 'shortName', 'paramsNum', 'default', 'hint']:
            if k not in measureConfig:
                raise KeyError(
                    f"Configuration '{k}' is lost, please fix missing of this parameter," +
                    " otherwise some errors may occur when calculating.")

        self.__name__ = self.measureConfig['name']
        self.shortName = self.measureConfig['shortName']
        self.paramsKey += measureBase.keys()

        if 'degree' not in measureConfig['default']:
            raise KeyError(f"This is neccessary parameter for this class.")

        # default create
        self.defaultANum = self.measureConfig['default']['degree']

        tmp = self.measureConfig['default'].copy()
        tmp.pop('degree')
        self.defaultOther = tmp

        # value create
        self.exps: dict[str: expsItem] = {}
        self.expsBelong = {}

        # reresh per calculation.
        self.now = argdict(
            params={
                'aNum': self.defaultANum,
                'paramsOther': self.defaultOther,
            },
            paramsKey=self.paramsKey,
        )
        self.IDNow = None

        self.multiNow = argdict(
            params={
                'configList': [],
                'shots': 1024,
            },
            paramsKey=[
                'name',
                'hashExpsName',
            ],
        )

    """Wave Function"""

    def addWave(
        self,
        waveCircuit: QuantumCircuit,
        key: Optional[any] = None,
    ) -> Optional[any]:
        """_summary_

        Args:
            waveCircuit (QuantumCircuit): _description_
            key (Optional[any], optional): _description_. Defaults to None.

        Returns:
            Optional[any]: _description_
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
        # TODO: Rewrite doc
        """Export wave function as `Operator`.

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
        # TODO: Rewrite doc
        """Export wave function as `Gate`.

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
        # TODO: Rewrite doc
        """Draw the circuit of wave function.

        Args:
            drawMethod (Optional[str], optional): Draw quantum circuit by 
                "text", "matplotlib", or "latex". Defaults to 'text'.
            decompose (Optional[int], optional): Draw quantum circuit with 
                `QuantumCircuit` be decomposed given times. Defaults to 0.

        Returns:
            Union[str, Figure]: The figure of wave function.
        """
        if wave == None:
            wave = self.lastWave

        qDummy = QuantumRegister(self.waves[wave].num_qubits, 'q')
        qcDummy = QuantumCircuit(qDummy)

        qcDummy.append(self.waveGate(wave), [
            qDummy[i] for i in range(self.waves[wave].num_qubits)])

        for t in range(decompose):
            qcDummy = qcDummy.decompose()

        fig = qcDummy.draw(drawMethod)

        return fig

    """Help & Hint"""

    def help(self) -> None:
        """Help.
        """

        print(f" ## {self.measureConfig['name']}")
        print(f"Required parameters number: {self.measureConfig['paramsNum']}")
        print(f"Required parameters:")
        for k, v in self.measureConfig['hint'].items():
            print(f" - {k}: {v}")
        print(f"otherHint: \n{self.measureConfig['otherHint']}")

    """Arguments and Parameters control"""

    @staticmethod
    def _aChecker(
        a: int,
        waveCircuit: QuantumCircuit,
    ) -> Exception:
        """Check whether the given degree of freedom is available.

        Args:
            a (int): The degree of freedom.

        Raises:
            IndexError: Raise when the degree of freedom is out of the number of qubits.
            ValueError: Raise when the degree of freedom is not a nature number.

        Returns:
            Exception: The Error from the value of the degree of freedom.
        """
        if a > waveCircuit.num_qubits:
            raise IndexError(
                f"The subsystem A includes {a} qubits beyond {waveCircuit.num_qubits} which the wave function has.")
        elif a < 0:
            raise ValueError(
                f"The number of qubits of subsystem A has to be natural number.")
        else:
            ...

    def _expIDDecider(
        self,
        expID: Optional[str] = None,
    ) -> str:
        """[summary]

        Args:
            expID (Optional[str], optional): [description]. Defaults to None.

        Raises:
            KeyError: [description]

        Returns:
            str: [description]
        """

        if expID != None:
            if expID in self.exps:
                tgtId = expID
            else:
                raise KeyError(
                    f"{expID} does not exist, '.IDNow' = {self.IDNow}.")
        else:
            tgtId = self.IDNow

        return tgtId

    def paramsControl(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        expID: Optional[str] = None,
        params: Union[list[int], dict[int], int, None] = None,
        runBy: str = "gate",
        shots: int = 1024,
        backend: Backend = Aer.get_backend('qasm_simulator'),
        drawMethod: Optional[str] = 'text',
        decompose: Optional[int] = 2,
        resultKeep: bool = False,
        dataRetrieve: dict[str: Union[list[str], str]] = None,
        provider: Optional[AccountProvider] = None,
        expsName: str = 'exps',
        tag: Optional[Union[tuple[str], str]] = None,
        transpileArgs: dict = {},
        **otherArgs: any
    ) -> tuple[str, argdict]:
        """Handling all arguments.

        Args:
            wave (Union[QuantumCircuit, int, None], optional): 
                The index of the wave function in `self.waves` or add new one to calaculation. 
                Defaults to None.
            expID (Optional[str], optional):
                Decide whether generate new id to initializw new experiment or continue current experiment. 
                True for createnew id, False for continuing current experiment.
                `if self.current == None` will create new id automatically, then giving a key 
                which exists in `self.exps` will switch to this experiment to operate it.
                Default to False.
            params (Union[list[int], dict[int], int, None], optional): 
                Parameters of experiment. Defaults to None.
            runBy (str, optional): 
                Construct wave function as initial state by `Operater` or `Gate`.
                Defaults to "gate".
            shots (int, optional): 
                Shots of the job.
                Defaults to 1024.
            backend (Backend, optional): 
                The quantum backend.
                Defaults to Aer.get_backend('qasm_simulator').
            drawMethod (Optional[str], optional): 
                Draw quantum circuit by "text", "matplotlib", or "latex".
                Defaults to 'text'.
            decompose (Optional[int], optional): 
                Running `QuantumCircuit` which be decomposed given times.
                Defaults to 2.
            resultKeep (bool, optional): 
                Whether to keep the results.
                Defaults to False.
            dataRetrieve (bool, optional): 
                Data to collect results from IBMQ via `IBMQJobManager`. 
                Defaults to None.
            provider (Optional[AccountProvider], optional): 
                `AccountProvider` of current backend for running `IBMQJobManager`. 
                Defaults to None.
            expsName (str, optional):
                Name this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to None.
            tag (Optional[Union[list[any], any]], optional):
                Given the experiment multiple tag to make a dictionary for recongnizing it.

        Raises:
            ValueError: When `waveFunction` is neither `int` nor ` QuantumCircuit`
            KeyError: Given `expID` does not exist.
            TypeError: When parameters are not all to be `int`.
            KeyError: CRITICAL ERROR OF MEASUREMENT.

        Returns:
            tuple[str, dict[str: any]]: Current `expID` and arguments.
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

        # expID
        if expID == None:
            self.IDNow = str(uuid4())
            print("Set key:", self.IDNow)
        elif expID == 'dummy':
            print('dummy test.')
        elif expID in self.exps:
            self.IDNow = expID
        elif expID == False:
            ...
        else:
            raise KeyError(f"{expID} does not exist, '.IDNow' = {self.IDNow}.")

        # params
        autofilledHint = (
            "Required '{}' but got {} params, " +
            "autofilled by default params, for more info using '.help()'."
        )

        if isinstance(params, int):
            self._aChecker(params)
            aNum = params
            paramsOther = self.defaultOther

        elif isinstance(params, list):
            for aItem in params:
                if not isinstance(aItem, int):
                    raise TypeError(
                        f"The values of configuration has to be 'int'," +
                        f" but we got '{type(aItem)}' at '{params.index(aItem)}'."
                    )

            aNum = params[0]
            self._aChecker(aNum)
            paramsOther = {k: v for k, v in zip(
                self.measureConfig['default'], params[1:])}

            if len(params) < self.measureConfig['paramsNum']:
                print(autofilledHint.format(
                    self.measureConfig['paramsNum'], len(params)))
                paramsOther = {**paramsOther, **self.defaultOther}

        elif isinstance(params, dict):
            if not 'degree' in params:
                raise KeyError(
                    "The given params lost degree of freedom/"
                )
            aNum = params['degree']

            if len(params) < self.measureConfig['paramsNum']:
                print(autofilledHint.format(
                    self.measureConfig['paramsNum'], len(params)))

            paramsOther = {
                **self.defaultOther, **params
            }

        else:
            warnings.warn("The format of the parameter is invalid.")
            self.help()
            aNum = self.defaultANum
            paramsOther = self.defaultOther

        # runBy
        if isinstance(backend, IBMQBackend):
            runByFixer = 'gate'
            print(
                "When use 'IBMQBackend' only allowed to use wave function as Gate instead of Operator.")
        else:
            runByFixer = runBy

        # tag
        if tag in self.expsBelong:
            self.expsBelong[tag].append(self.IDNow)
        else:
            self.expsBelong[tag] = [self.IDNow]

        # Export all arguments
        self.now = argdict(
            params={
                'aNum': aNum,
                'paramsOther': paramsOther,

                'wave': wave,
                'expID': self.IDNow,
                'params': params,
                'runBy': runByFixer,
                'shots': shots,
                'backend': backend,
                'drawMethod': drawMethod,
                'decompose': decompose,
                'resultKeep': resultKeep,
                'dataRetrieve': dataRetrieve,
                'provider': provider,
                'expsName': expsName,
                'tag': tag,
                'transpileArgs': transpileArgs,

                **otherArgs,
            },
            paramsKey=self.paramsKey,
        )

        return self.IDNow, self.now

    def paramsControlDoc(f: Callable) -> Callable:
        """Pass the additional doc of the arguments of `self.paramsControl`
        to the function used it.

        Args:
            f (Callable): Function use `self.paramsControl`.

        Returns:
            Callable: Function use `self.paramsControl`.
        """

        def wrapper(self, *args, **kwargs):
            paramsControlArgsDoc = f"""
        
            DocString of `paramsControl`:
            {self.paramsControl.__doc__}
        
            """
            docs = f.__doc__
            if isinstance(docs, type(None)):
                docs = """
                Args:
                    {paramsControlArgsDoc}
                """.format(paramsControlArgsDoc=paramsControlArgsDoc)
            else:
                docs.format(paramsControlArgsDoc=paramsControlArgsDoc)
            docs.format(paramsControlArgsDoc=paramsControlArgsDoc)
            f.__doc__ = docs

            return f(self, *args, **kwargs)
        return wrapper

    """ Main Process: Circuit"""

    @staticmethod
    def qcDecomposer(
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

    def drawCircuit(
        self,
        expID: Optional[str] = None,
        drawMethod: Optional[str] = 'text',
        decompose: Optional[int] = 0,
    ) -> Union[str, Figure]:
        """Drawing the circuit figure of the experiment

        Args:
            expID (Optional[str]): The unique id of experiment, by uuid4.
            drawMethod (Optional[str], optional): Draw quantum circuit by
                "text", "matplotlib", or "latex". Defaults to 'text'.
            decompose (Optional[int], optional): Decide the times of decomposing the circuit.
                Draw quantum circuit with composed circuit. Defaults to 0.

        Raises:
            KeyError: When 'expID' is not given or not existed.

        Returns:
            Union[str, Figure]: The figure of quantum circuit.
        """

        tgtId = self._expIDDecider(expID=expID)

        qcExp = self.exps[tgtId]['circuit']
        if isinstance(qcExp, list):
            fig = []
            for qc in qcExp:
                qc = self.qcDecomposer(qc, decompose)
                fig.append(qc.draw(drawMethod))

        elif isinstance(qcExp, QuantumCircuit):
            qcExp = self.qcDecomposer(qcExp, decompose)
            fig = qcExp.draw(drawMethod)

        return fig

    def circuitMethod(
        self,
    ) -> Union[QuantumCircuit, list[QuantumCircuit]]:
        """The method to construct circuit.

        Returns:
            Union[QuantumCircuit, list[QuantumCircuit]]: 
                The quantum circuit of experiment.
        """
        args = self.now
        numQubits = self.waves[args.wave].num_qubits

        qFunc1 = QuantumRegister(numQubits, 'q1')
        cMeas = ClassicalRegister(numQubits, 'c1')
        qcExp = QuantumCircuit(qFunc1, cMeas)

        qcExp.append(self.waveInstruction(
            wave=args.wave,
            runBy=args.runBy,
            backend=args.backend,
        ), [qFunc1[i] for i in range(numQubits)])

        for i in range(args.aNum):
            qcExp.measure(qFunc1[i], cMeas[i])
        print("It's default circuit, the quantum circuit is not yet configured.")

        return qcExp

    @paramsControlDoc
    def circuitOnly(
        self,
        **allArgs: any,
    ) -> Union[QuantumCircuit, list[QuantumCircuit]]:
        """Construct the quantum circuit of experiment.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.
            {paramsControlArgsDoc}

        Raises:
            IndexError: Raise when the degree of freedom is out of the number of qubits.
            ValueError: Raise when the degree of freedom is not a nature number.

        Returns:
            QuantumCircuit: The quantum circuit of experiment.
        """

        IDNow, argsNow = self.paramsControl(**allArgs)
        qcExp = self.circuitMethod()

        self.exps[IDNow] = measureBase.make({
            'expID': IDNow,
            'circuit': qcExp,

            **argsNow,
        })

        fig = self.drawCircuit(
            drawMethod=argsNow.drawMethod,
            decompose=argsNow.decompose,
        )
        self.exps[IDNow] = {
            **self.exps[IDNow],
            'fig': fig,
        }

        return qcExp

    """ Main Process: Data Import and Export"""

    @staticmethod
    def _quickName(
        aNum: int,
        other: dict[str: int] = {},
    ) -> str:
        """Generate name for each experiment from `degree` and `paramsOther`.

        Args:
            aNum (int): `degree`, the degree of the freedom.
            other (dict[str: int]): `paramsOther`, other parameters required by measurement.

        Returns:
            str: the name of the experiment.
        """

        paramsStr = '-'.join([f'{v}' for k, v in other.items()])
        return f'{aNum}_{paramsStr}'

    def writeLegacy(
        self,
        saveLocation: Optional[Union[Path, str]] = None,
        expID: Optional[str] = None,
        exceptItems: Optional[list[str]] = None,
        overWrite: bool = False,
    ) -> dict[str: any]:
        """Export the experiment data.

        Args:
            saveLocation (Optional[Union[Path, str]], optional):
                Where to save the export content as `json` file.
                If `saveLocation == None`, then cancelled the file to be exported.
                Defaults to None.
            expID (Optional[str], optional): 
                The id of the experiment will be exported.
                If `expID == None`, then export the experiment which id is`.IDNow`.
                Defaults to None.
            exceptItems (Optional[list[str]], optional):
                The keys will be excluded. Defaults to None.

        Returns:
            dict[str: any]: the export content.
        """

        tgtID = self._expIDDecider(expID=expID)
        aNum = self.exps[tgtID]['aNum']
        paramsOther = self.exps[tgtID]['paramsOther']

        expName = self.exps[tgtID]['expsName']
        saveLocParts = Path(saveLocation).parts
        saveLoc = Path(saveLocParts[0]) if len(
            saveLocParts) > 0 else Path('./')
        for p in saveLocParts[1:]:
            saveLoc /= p
        saveLoc /= expName

        filename = f'dim={self._quickName(aNum, paramsOther)}.Id={tgtID}.json'
        self.exps[tgtID]['filename'] = Path(filename).name

        exportItems = jsonablize(self.exps[tgtID])
        if isinstance(exceptItems, list):
            actualDrop = []
            for k in exceptItems:
                if k not in neccessaryKey:
                    if k in exportItems:
                        exportItems.pop(k)
                        actualDrop.append(k)
                    else:
                        ...
                        # print(f"{k} is not in export content.")
                else:
                    print(f"'{k}' is neccessary.")
            if len(actualDrop) > 0:
                print(f"The following keys have been dropped:", actualDrop)

        if isinstance(saveLocation, (Path, str)):
            if not os.path.exists(saveLoc):
                os.mkdir(saveLoc)

            overWriteOuput = 'w+' if overWrite else 'w'
            with open((saveLoc / filename), overWriteOuput, encoding='utf-8') as Legacy:
                json.dump(exportItems, Legacy, indent=2, ensure_ascii=False)

        else:
            print(
                "'saveLocation' is not the type of 'str' or 'Path', " +
                "so export cancelled.")

        self.exps[tgtID] = {
            **self.exps[tgtID],
            'saveLocation': saveLocation,
            'exceptItems': exceptItems,
        }

        return exportItems

    def readLegacy(
        self,
        filename: Optional[Union[Path, str]] = None,
        saveLocation: Union[Path, str] = Path('./'),
        expID: Optional[str] = None,
    ) -> dict[str: any]:
        """Read the experiment data.

        Raises:
            FileNotFoundError: When `saveLocation` is not available.
            TypeError: File content is not `dict`.

        Returns:
            dict[str: any]: The data.
        """

        if isinstance(saveLocation, (Path)):
            ...
        elif isinstance(saveLocation, (str)):
            saveLocation = Path(saveLocation)
        else:
            warnings.warn("Invalid path. reset as './'.")
            saveLocation = Path('./')

        if not os.path.exists(saveLocation):
            raise FileNotFoundError("Such location not found.")

        dataRead = {}
        if expID != None:
            lsfolder = glob.glob(str(saveLocation / f"*{expID}*.json"))
            if len(lsfolder) == 0:
                print(f"'{expID}' does not exist.")
            for p in lsfolder:
                with open(p, 'r', encoding='utf-8') as Legacy:
                    dataRead = json.load(Legacy)
                    print(p, 'file found.')

        elif isinstance(filename, (str, Path)):
            if os.path.exists(saveLocation / filename):
                with open(saveLocation / filename, 'r', encoding='utf-8') as Legacy:
                    dataRead = json.load(Legacy)
                    print(saveLocation / filename, 'file found.')
            else:
                print(f"'{(saveLocation / filename)}' does not exist.")

        else:
            raise FileNotFoundError(f"The file 'expID={expID}' not found.")

        if len(dataRead) == 0:
            ...
        if isinstance(dataRead, dict):
            self.exps[dataRead["expID"]] = dataRead
            if measureBase.ready(dataRead):
                ...
            else:
                lost = measureBase.check(dataRead)
                warnings.warn(f"Key Lost: {lost}")
        else:
            raise TypeError("The export file does not match the type 'dict'.")

        if "tag" in dataRead:
            dataRead["tag"] = tuple(dataRead["tag"]) if isinstance(
                dataRead["tag"], list) else dataRead["tag"]

        return dataRead

    """ Main Process: Job Create"""

    @paramsControlDoc
    def jobOnly(
        self,
        **allArgs: any,
    ) -> tuple[BaseJob, list[str]]:
        """Export the job of experiments.

        https://github.com/Qiskit/qiskit-terra/issues/4778
        According to this issue, `IBMQJobManager` will automatically splits off job to fit the backend limit 
        and combines the result, so this version `jobOnly` will ignore the problem on the number of jobs
        larger than backends limits.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.
            {paramsControlArgsDoc}

        Returns:
            tuple[list[Union[BaseJob, ManagedJobSet]], list[str]]:
                Construnct the quantum computing job and return the job id.
        """

        qcExp = self.circuitOnly(**allArgs)
        IDNow, argsNow = self.IDNow, self.now

        circs = qcExp if isinstance(qcExp, list) else [qcExp]
        circs = [self.qcDecomposer(qc, argsNow.decompose) for qc in circs]
        circs = transpile(
            circs,
            backend=argsNow.backend,
            **argsNow.transpileArgs,
        )

        jobExecution = execute(
            circs,
            backend=argsNow.backend,
            shots=argsNow.shots
        )
        jobID = jobExecution.job_id()

        self.exps[IDNow] = {
            **self.exps[IDNow],
            'jobID': jobID,
        }

        return jobExecution, jobID

    """ Main Process: Calculation and Result"""

    @paramsControlDoc
    def runOnly(
        self,
        **allArgs: any,
    ) -> Optional[list[dict]]:
        """Export the result after running the job.
        - At same position with `self.retrieveOnly()` in the process.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.
            {paramsControlArgsDoc}

        Returns:
            Optional[list[dict]]: The result of the job.
        """

        job: BaseJob
        jobID: list[str]
        job, jobID = self.jobOnly(**allArgs)
        IDNow, argsNow = self.IDNow, self.now

        result = job.result()

        self.exps[IDNow] = {
            **self.exps[IDNow],

            "jobID": jobID,
            "name": self._quickName(argsNow.aNum, argsNow.paramsOther),
        }
        return result

    # TODO: Required Remake
    @paramsControlDoc
    def retrieveOnly(
        self,
        **allArgs: any,
    ) -> Optional[list[dict]]:
        """Retrieve the data from IBMQService which is already done, and add it into `self.exps`.
        - At same position with `self.runOnly()` in the process.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.
            {paramsControlArgsDoc}

        Raises:
            KeyError: The necessary keys in `self.now.dataRetrieve` are lost.
                When the job record does not have `jobId`.
            ValueError: `argsNow.dataRetrieve` is null.

        Returns:
            Optional[list[dict]]: The result of the job.
        """

        IDNow, argsNow = self.paramsControl(**allArgs)
        if not isinstance(argsNow.provider, AccountProvider):
            raise ValueError("Provider required.")

        jobLegend = measureBase.make()
        if IDNow in self.exps:
            jobLegend = self.exps[IDNow]

        if isinstance(argsNow.dataRetrieve, dict):
            lost = measureBase.check(argsNow.dataRetrieve)
            for k in lost:
                if k in ["jobID", "IBMQJobManager"]:
                    raise KeyError(
                        f"The giving data to retrieve jobs needs the key '{k}'")
            jobLegend = argsNow.dataRetrieve

        elif isinstance(argsNow.dataRetrieve, str):
            jobLegend["jobID"] = [argsNow.dataRetrieve]

        else:
            raise ValueError("The giving data to retrieve jobs can't be null.")

        result = None
        for singleJob in jobLegend["jobID"]:
            try:
                retrieved = IBMQJobManager().retrieve_job_set(
                    job_set_id=singleJob,
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

        self.exps[IDNow] = {
            **self.exps[IDNow],

            "jobID": jobLegend["jobID"],
            "name": jobLegend["jobID"],

            'aNum': None,
            'paramsOther': None,

            'wave': None,
            'expID': self.IDNow,
            'params': None,
            'runBy': None,
            'shots':  None,
            'backend':  None,
            'drawMethod':  None,
            'decompose':  None,

            **jobLegend,
        }
        return result

    """ Main Process: Purity and Entropy"""

    @staticmethod
    def purityMethod(
        aNum: int,
        paramsOther: dict[str: int],
        shots: int,
        result: Union[Result, ManagedResults],
        resultIdxList: Optional[list[int]] = None,
    ) -> tuple[dict[str, float], float, float]:
        """Computing Purity and Entropy.

        Returns:
            tuple[dict[str, float], float, float]: 
                Counts, purity, entropy of experiment.
        """

        if resultIdxList == None:
            resultIdxList = [0]
        else:
            ...

        counts = result.get_counts(resultIdxList[0])
        purity = -100
        entropy = -100
        return counts, purity, entropy

    @paramsControlDoc
    def purityOnly(
        self,
        dataRetrieve: dict[str: Union[list[str], str]] = None,
        **allArgs: any,
    ) -> tuple[Optional[float], Optional[float]]:
        """Export the result which completed calculating purity.

        Args:
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.
            {paramsControlArgsDoc}

        Returns:
            tuple[Optional[float], Optional[float]]: the purity and the entropy.
        """

        resultExecution = (
            self.retrieveOnly if dataRetrieve != None else self.runOnly
        )(
            dataRetrieve=dataRetrieve,
            **allArgs,
        )
        IDNow, argsNow = self.IDNow, self.now

        print("# "+"-"*30)
        print(f"# Calculating {self.__name__}...")
        print(f"# name: {self._quickName(argsNow.aNum, argsNow.paramsOther)}")
        print(f"# id: {self.IDNow}")

        counts, purity, entropy = self.purityMethod(
            aNum=argsNow.aNum,
            paramsOther=argsNow.paramsOther,
            shots=argsNow.shots,
            result=resultExecution,
        )

        if argsNow.resultKeep:
            self.exps[IDNow]['result'] = resultExecution
            warnings.warn(
                "Result will keep, but it may cause memory overallocated.")
        else:
            print("Entropy and Purity are figured out, result will clear.")
            del self.exps[IDNow]['result']

        print(f"# {self.__name__} completed")
        print(f"# name: {self._quickName(argsNow.aNum, argsNow.paramsOther)}")
        print(f"# id: {self.IDNow}")
        print("End..."+"\n"*2)

        self.exps[IDNow] = {
            **self.exps[IDNow],
            'counts': counts,
            'purity': purity,
            'entropy': entropy,
        }
        gc.collect()

        return purity, entropy

    """ Main Process: Main Control"""

    @paramsControlDoc
    def output(
        self,
        saveLocation: Union[Path, str, None] = None,
        exceptItems: Optional[list[str]] = None,
        **allArgs: any,
    ) -> list[str]:
        """[summary]

        Args:
            saveLocation (Optional[Union[Path, str]], optional):
                Where to save the export content as `json` file.
                If `saveLocation == None`, then cancelled the file to be exported.
                Defaults to None.
            exceptItems (Optional[list[str]], optional):
                The keys will be excluded. Defaults to None.
            allArgs: all arguments will handle by `self.paramsControl()` and export as specific format.
            {paramsControlArgsDoc}

        Returns:
            dict: all result of experiment.
        """

        self.purityOnly(**allArgs)
        IDNow, argsNow = self.IDNow, self.now

        if isinstance(saveLocation, (Path, str)):
            curLegacy = self.writeLegacy(
                saveLocation=saveLocation,
                expID=IDNow,
                exceptItems=exceptItems
            )
        else:
            curLegacy = None

        return self.exps[IDNow]

    """ MultiJobs """

    @staticmethod
    def _multiExportName(
        expsName: str,
        saveLocation: Union[Path, str] = './',
        isRetrieve: bool = False,
        shortName: Optional[str] = None,
    ) -> tuple[int, str, Path]:
        """_summary_

        Args:
            expsName (str): _description_
            saveLocation (Union[Path, str], optional): _description_. Defaults to './'.

        Returns:
            tuple[int, str, Path]: _description_
        """
        indexRename = 1

        if isRetrieve:
            hashExpsName = expsName
            expExportLoc = Path(saveLocation) / hashExpsName
            print(expExportLoc, 'retrieve', hashExpsName)

        else:
            shortNameAdder = f'{expsName}.' + \
                shortName if shortName != None else expsName
            hashExpsName = f"{shortNameAdder}.{str(indexRename).rjust(3,'0')}"
            expExportLoc = Path(saveLocation) / hashExpsName
            while os.path.exists(expExportLoc):
                print(f'{expExportLoc} is repeat name')
                indexRename += 1
                hashExpsName = f"{shortNameAdder}.{str(indexRename).rjust(3,'0')}"
                expExportLoc = Path(saveLocation) / hashExpsName
            print(expExportLoc, 'hash', hashExpsName)
            os.makedirs(expExportLoc)

        def Naming(filename: str) -> Callable:
            return expExportLoc.joinpath(f"{hashExpsName}.{filename}")

        return indexRename, hashExpsName, expExportLoc, Naming

    def paramsControlMulti(
        self,
        configList: list[dict[str: any]] = [],
        backend: Optional[Backend] = None,
        shots: int = 1024,
        saveLocation: Union[Path, str] = './',
        expsName: Union[Path, str] = 'exps',
        exceptItems: list[str] = [],
        independentExports: bool = False,

        isRetrieve: bool = False,
        powerJobID: str = '',
        provider: Optional[AccountProvider] = None,
        dataPowerJobs: dict[any] = {},

        addShortName: bool = True,
        transpileArgs: dict[str] = {},
        **otherArgs,
    ) -> argdict:
        """_summary_

        Args:
            configList (_type_): _description_
            backend (Backend): _description_
            shots (int, optional): _description_. Defaults to 1024.
            saveLocation (Union[Path, str], optional): _description_. Defaults to './'.
            expsName (Union[Path, str], optional): _description_. Defaults to 'exps'.
            exceptItems (Optional[list[str]], optional): _description_. Defaults to None.
            independentExports (bool, optional): _description_. Defaults to False.

        Returns:
            argdict: _description_
        """

        indexRename, hashExpsName, expExportLoc, Naming = self._multiExportName(
            expsName=expsName,
            saveLocation=saveLocation,
            isRetrieve=isRetrieve,
            shortName=(self.shortName if addShortName else None),
        )

        self.multiNow = argdict(
            params={
                'configList': configList,
                'backend': backend,
                'shots': shots,
                'saveLocation': saveLocation,
                'expsName': expsName,
                'exceptItems': exceptItems+[
                    'fig', 'circuit', 'Naming',
                ],
                'independentExports': independentExports,

                'expExportLoc': expExportLoc,
                'hashExpsName': hashExpsName,
                'Naming': Naming,
                'transpileArgs': transpileArgs,
                **otherArgs,
            },
            paramsKey=[
                'name',
                'hashExpsName',
                'exportLocation',
                'expIDList',
                'fileList',

            ],
        )

        return self.multiNow

    # TODO: DocString of paramsControMulti decorator

    def multiOutputs(
        self,
        **allArgs: any,
    ) -> tuple[dict[any], dict[list[float]], dict[list[float]]]:
        """_summary_

        Returns:
            tuple[ManagedJobSet, str, dict[any]]: _description_
        """

        argsMulti = self.paramsControlMulti(**allArgs)
        Naming = argsMulti.Naming

        fileList = []
        expIDList = []
        expPurityList = { 'all': [], 'noTags': [] }
        expEntropyList = { 'all': [], 'noTags': [] }
        expTagsMapping = { 'noTags': [] }
        expsBelong = {}
        gitignore = syncControl()

        initedConfigList = [
            qurrentConfig.make({
                **config,
                'expsName': argsMulti.hashExpsName,
                'backend': argsMulti.backend,
                'shots': argsMulti.shots,
            })
            for config in argsMulti.configList]

        for config in initedConfigList:
            purity, entropy = self.purityOnly(**config)
            IDNow = self.IDNow

            curLegacy = self.writeLegacy(
                saveLocation=argsMulti.saveLocation,
                expID=IDNow,
                exceptItems=argsMulti.exceptItems,
            )
            fileList.append(curLegacy['filename'])
            expIDList.append(IDNow)
            expPurityList['all'].append(purity)
            expEntropyList['all'].append(entropy)
            
            curLegacyTag = tuple(curLegacy['tag']) if isinstance(
                curLegacy['tag'], list) else curLegacy['tag']
            
            if curLegacyTag == 'all':
                curLegacyTag == None
                print("'all' is a reserved key for export data.")
            elif curLegacyTag == 'noTags':
                curLegacyTag == None
                print("'noTags' is a reserved key for export data.")
            
            if curLegacyTag == None:
                expTagsMapping['noTags'].append(len(expPurityList['all'])-1)
                expPurityList['noTags'].append(purity)
                expEntropyList['noTags'].append(entropy)
            elif curLegacyTag in expsBelong:
                expsBelong[curLegacyTag].append(IDNow)
                expTagsMapping[curLegacyTag].append(len(expPurityList['all'])-1)
                expPurityList[curLegacyTag].append(purity)
                expEntropyList[curLegacyTag].append(entropy)
            else:
                expsBelong[curLegacyTag] = [IDNow]
                expTagsMapping[curLegacyTag] = [len(expPurityList['all'])-1]
                expPurityList[curLegacyTag] = [purity]
                expEntropyList[curLegacyTag] = [entropy]
            
        gitignore.ignore('*.json')

        dataMultiJobs = {
            **argsMulti.jsonize(),

            'name': argsMulti.hashExpsName,
            'hashExpsName': argsMulti.hashExpsName,
            'exportLocation': argsMulti.expExportLoc,
            
            'expIDList': expIDList,
            'fileList': fileList,
            'purityList': expPurityList,
            'entropyList': expEntropyList,
            
            'expsBelong': expsBelong,
            'expTagsMapping': expTagsMapping,
        }

        quickJSONExport(content=dataMultiJobs, filename=Naming(
            'multiJobs.json'), mode='w+', jsonablize=True)
        gitignore.sync('*.multiJobs.json')
        quickJSONExport(content=expPurityList, filename=Naming(
            'purityList.json'), mode='w+', jsonablize=True)
        gitignore.sync('*.multiJobs.json')
        quickJSONExport(content=expEntropyList, filename=Naming(
            'entropyList.json'), mode='w+', jsonablize=True)
        gitignore.sync('*.multiJobs.json')

        if argsMulti.independentExports:
            quickJSONExport(content=expIDList, filename=Naming(
                'expIDList.json'), mode='w+')
            gitignore.sync('*.expIDList.json')
            quickJSONExport(content=fileList, filename=Naming(
                'fileList.json'), mode='w+')
            gitignore.sync('*.fileList.json')

        gitignore.export(argsMulti.expExportLoc)

        return dataMultiJobs, expPurityList, expEntropyList

    def multiRead(
        self,
        expsName: Union[Path, str],
        isRetrieve: bool = True,
        powerJobID: str = '',
        provider: Optional[AccountProvider] = None,
        saveLocation: Union[Path, str] = './',
        **otherArgs,
    ) -> tuple[NoneType, str, dict[any], list[float], list[float]]:
        """Require to read the file exported by `.powerJobsPending`.

        Args:
            expsName (Optional[Union[Path, str]]): The folder name of the job wanted to import.
            powerJobID (str, optional):Job Id. Defaults to ''.
            provider (Optional[AccountProvider], optional): The provider of the backend used by job. Defaults to None.
            saveLocation (Union[Path, str], optional): The location of the folder of the job wanted to import. Defaults to './'.

        Raises:
            ValueError: When file is broken.

        Returns:
            tuple[NoneType, str, dict[any], list[float], list[float]]: The result of `IBMQJobManager`,
                its job id, and the data of entire job set.
        """

        argsMulti = self.paramsControlMulti(
            powerJobID=powerJobID,
            provider=provider,
            saveLocation=saveLocation,
            expsName=expsName,
            isRetrieve=isRetrieve,
            **otherArgs,
        )
        Naming = argsMulti.Naming

        dataDummyJobs: dict[any] = {}
        dataDummyJobs['powerJobID'] = powerJobID
        expPurityList = []
        expEntropyList = []
        expsBelong = {}

        if (expsName == None):
            raise ValueError("'expsName' required.")
        else:
            dataPowerJobsName = Naming('powerJobs.json')
            dataMultiJobsName = Naming('multiJobs.json')
            if os.path.exists(dataPowerJobsName):
                with open(dataPowerJobsName, 'r', encoding='utf-8') as theData:
                    dataDummyJobs = json.load(theData)

                for k in ['circsMapDict', 'powerJobID']:
                    if not k in dataDummyJobs:
                        raise ValueError("File broken.")

            elif os.path.exists(dataMultiJobsName):
                with open(dataMultiJobsName, 'r', encoding='utf-8') as theData:
                    dataDummyJobs = json.load(theData)

            else:
                with open(Naming('configList.json'), 'r', encoding='utf-8') as File:
                    dataDummyJobs['configList'] = json.load(File)

                with open(Naming('expIDList.json'), 'r', encoding='utf-8') as File:
                    dataDummyJobs['expIDList'] = json.load(File)

                with open(Naming('circsMapDict.json'), 'r', encoding='utf-8') as File:
                    dataDummyJobs['circsMapDict'] = json.load(File)

                if os.path.exists(Naming('powerJobID.csv')):
                    with open(Naming('powerJobID.csv'), 'r', encoding='utf-8') as File:
                        content = File.readlines()
                        dataDummyJobs['powerJobID'] = content[0][:-1]

            for p in dataDummyJobs['expIDList']:
                self.readLegacy(
                    saveLocation=argsMulti.expExportLoc,
                    expID=p,
                )

            if 'purityList' in dataDummyJobs:
                expPurityList = keyTupleLoads(dataDummyJobs['purityList'])
            if 'entropyList' in dataDummyJobs:
                expEntropyList = keyTupleLoads(dataDummyJobs['entropyList'])
            if 'expsBelong' in dataDummyJobs:
                expsBelong = keyTupleLoads(dataDummyJobs['expsBelong'])
                self.expsBelong = {
                    **self.expsBelong, **expsBelong,
                }
                dataDummyJobs['expsBelong'] = expsBelong

        return None, powerJobID, dataDummyJobs, expPurityList, expEntropyList

    """`IBMQJobManager` multiOutputs"""

    def powerJobsPending(
        self,
        **allArgs: any,
    ) -> tuple[ManagedJobSet, str, dict[any]]:
        """Require to read the file exported by `.powerJobsPending`.

        Returns:
            tuple[ManagedJobSet, str, dict[any]]: The result of `IBMQJobManager`,
                its job id, and the data of entire job set.
        """

        argsMulti = self.paramsControlMulti(**allArgs)
        Naming = argsMulti.Naming

        fileList = []
        expIDList = []
        numCircDict = {}
        circsMapDict = {}
        circs = []
        expsBelong = {}
        powerExps = {}
        gitignore = syncControl()

        initedConfigList = [
            qurrentConfig.make({
                **config,
                'expsName': argsMulti.hashExpsName,
                'backend': argsMulti.backend,
                'shots': argsMulti.shots,
            })
            for config in argsMulti.configList]

        for config in initedConfigList:
            qcExp = self.circuitOnly(**config)
            IDNow = self.IDNow

            if isinstance(qcExp, list):
                numCirc = len(qcExp)
            elif isinstance(qcExp, QuantumCircuit):
                numCirc = 1
            else:
                numCirc = 0
                warnings.warn(
                    f"The circuit output of '{IDNow}' is nor 'list' neither 'QuantumCircuit', " +
                    f"but '{type(qcExp)}'.")
            numCircDict[IDNow] = numCirc

            curLegacy = self.writeLegacy(
                saveLocation=argsMulti.saveLocation,
                expID=IDNow,
                exceptItems=argsMulti.exceptItems,
            )
            fileList.append(curLegacy['filename'])
            expIDList.append(IDNow)
            powerExps[IDNow] = curLegacy
            curLegacyTag = tuple(curLegacy['tag']) if isinstance(
                curLegacy['tag'], list) else curLegacy['tag']
            if curLegacyTag == None:
                ...
            elif curLegacyTag in expsBelong:
                expsBelong[curLegacyTag].append(IDNow)
            else:
                expsBelong[curLegacyTag] = [IDNow]
        gitignore.ignore('*.json')

        for idKey in expIDList:
            circsMapDict[idKey] = []
            if numCircDict[idKey] > 1:
                for c in range(numCircDict[idKey]):
                    circsMapDict[idKey].append(len(circs))
                    circs.append(self.exps[idKey]['circuit'][c])
            elif numCircDict[idKey] == 1:
                circsMapDict[idKey].append(len(circs))
                circs.append(self.exps[idKey]['circuit'])
            else:
                ...

        circs = [qc.decompose().decompose() for qc in circs]
        circs = transpile(
            circs,
            backend=argsMulti.backend,
            **argsMulti.transpileArgs,
        )

        powerJob = IBMQJobManager().run(
            experiments=circs,
            backend=argsMulti.backend,
            shots=argsMulti.shots,
            name=f'{argsMulti.hashExpsName}_w/_{len(circs)}_jobs'
        )
        powerJobID = powerJob.job_set_id()

        dataPowerJobs = {
            **argsMulti.jsonize(),

            'name': argsMulti.hashExpsName,
            'hashExpsName': argsMulti.hashExpsName,
            'exportLocation': argsMulti.expExportLoc,
            'expIDList': expIDList,
            'fileList': fileList,
            'expsBelong': expsBelong,

            'ibmq_job_name': f'{argsMulti.hashExpsName}_w/_{len(circs)}_jobs',
            'circsMapDict': circsMapDict,
            'powerJobID': powerJobID,
        }

        quickJSONExport(content=dataPowerJobs, filename=Naming(
            'powerJobs.json'), mode='w+', jsonablize=True)
        gitignore.sync('*.powerJobs.json')

        if argsMulti.independentExports:
            quickJSONExport(content=expIDList, filename=Naming(
                'expIDList.json'), mode='w+')
            gitignore.sync('*.expIDList.json')
            quickJSONExport(content=dataPowerJobs['configList'], filename=Naming(
                'configList.json'), mode='w+')
            gitignore.sync('*.configList.json')
            quickJSONExport(content=circsMapDict, filename=Naming(
                'circsMapDict.json'), mode='w+')
            gitignore.sync('*.circsMapDict.json')
            quickJSONExport(content=fileList, filename=Naming(
                'fileList.json'), mode='w+')
            gitignore.sync('*.fileList.json')
            with open(Naming('powerJobID.csv'), 'w+', encoding='utf-8') as theFile:
                print(f"{powerJobID}", file=theFile)
                print(f"{Naming('powerJobID.csv')}' saved.")

        gitignore.export(argsMulti.expExportLoc)

        return powerJob, powerJobID, dataPowerJobs

    def powerJobsRetreive(
        self,
        expsName:  Optional[Union[Path, str]],
        powerJobID: str = '',
        provider: Optional[AccountProvider] = None,
        saveLocation: Optional[Union[Path, str]] = './',
        **otherArgs,
    ) -> tuple[ManagedJobSet, str, dict[any]]:
        """Require to read the file exported by `.powerJobsPending`.

        Args:
            expsName (Optional[Union[Path, str]]): The folder name of the job wanted to import.
            powerJobID (str, optional):Job Id. Defaults to ''.
            provider (Optional[AccountProvider], optional): The provider of the backend used by job. Defaults to None.
            saveLocation (Optional[Union[Path, str]], optional): The location of the folder of the job wanted to import. Defaults to './'.

        Raises:
            ValueError: When file is broken.

        Returns:
            tuple[ManagedJobSet, str, dict[any]]: The result of `IBMQJobManager`,
                its job id, and the data of entire job set.
        """

        powerJob, powerJobID, dataPowerJobs, _, _ = self.multiRead(
            powerJobID=powerJobID,
            provider=provider,
            saveLocation=saveLocation,
            expsName=expsName,
            **otherArgs,
        )

        powerJob = IBMQJobManager().retrieve_job_set(
            job_set_id=dataPowerJobs['powerJobID'],
            provider=provider,
        )

        return powerJob, powerJobID, dataPowerJobs

    def powerJobsOutputs(
        self,
        isRetrieve: bool = False,
        **allArgs: any,
    ) -> tuple[dict[any], dict[list[float]], dict[list[float]]]:
        """_summary_

        Returns:
            list[str]: _description_
        """

        expPurityList = { 'all': [], 'noTags': [] }
        expEntropyList = { 'all': [], 'noTags': [] }
        expTagsMapping = { 'noTags': [] }
        gitignore = syncControl()

        powerJob: ManagedJobSet
        powerJob, powerJobID, dataPowerJobs = (
            self.powerJobsRetreive if isRetrieve else self.powerJobsPending
        )(**allArgs, isRetrieve=isRetrieve)

        argsMulti = self.multiNow
        Naming = argsMulti.Naming
        expIDList = dataPowerJobs['expIDList']
        circsMapDict = dataPowerJobs['circsMapDict']

        powerResultRaw: ManagedResults = powerJob.results()
        powerResult: Result = powerResultRaw.combine_results()

        print("# "+"-"*30)
        print(f"# Calculating {self.__name__}...")
        print(f"# ExpNames: {argsMulti.hashExpsName}")
        print(f"# id: {powerJobID}")

        for expID in expIDList:
            counts, purity, entropy = self.purityMethod(
                aNum=self.exps[expID]['aNum'],
                paramsOther=self.exps[expID]['paramsOther'],
                shots=self.exps[expID]['shots'],
                result=powerResult,
                resultIdxList=circsMapDict[expID],
            )
            self.exps[expID]['counts'] = counts
            self.exps[expID]['entropy'] = entropy
            self.exps[expID]['purity'] = purity

            curLegacy = self.writeLegacy(
                saveLocation=argsMulti.saveLocation,
                expID=expID,
                exceptItems=argsMulti.exceptItems,
                overWrite=True,
            )
            expPurityList['all'].append(purity)
            expEntropyList['all'].append(entropy)
            
            curLegacyTag = tuple(curLegacy['tag']) if isinstance(
                curLegacy['tag'], list) else curLegacy['tag']

            if curLegacyTag == 'all':
                curLegacyTag == None
                print("'all' is a reserved key for export data.")
            elif curLegacyTag == 'noTags':
                curLegacyTag == None
                print("'noTags' is a reserved key for export data.")
            
            if curLegacyTag == None:
                expTagsMapping['noTags'].append(len(expPurityList['all'])-1)
                expPurityList['noTags'].append(purity)
                expEntropyList['noTags'].append(entropy)
            elif curLegacyTag in expTagsMapping:
                expTagsMapping[curLegacyTag].append(len(expPurityList['all'])-1)
                expPurityList[curLegacyTag].append(purity)
                expEntropyList[curLegacyTag].append(entropy)
            else:
                expTagsMapping[curLegacyTag] = [len(expPurityList['all'])-1]
                expPurityList[curLegacyTag] = [purity]
                expEntropyList[curLegacyTag] = [entropy]

        dataPowerJobsName = Naming('powerJobs.json')
        with open(dataPowerJobsName, 'w', encoding='utf-8') as theData:
            dataPowerJobs = {
                **dataPowerJobs,
                'purityList': expPurityList,
                'entropyList': expEntropyList,
            }
            json.dump(jsonablize(dataPowerJobs), theData, indent=2, ensure_ascii=False)
        quickJSONExport(content=expPurityList, filename=Naming(
            'purityList.json'), mode='w+', jsonablize=True)
        gitignore.sync('*.multiJobs.json')
        quickJSONExport(content=expEntropyList, filename=Naming(
            'entropyList.json'), mode='w+', jsonablize=True)
        gitignore.sync('*.multiJobs.json')

        gitignore.ignore('*.json')
        gitignore.sync('*.multiJobs.json')
        gitignore.sync('*.powerJobs.json')
        gitignore.sync('*.expIDList.json')
        gitignore.sync('*.configList.json')
        gitignore.sync('*.circsMapDict.json')
        gitignore.sync('*.fileList.json')
        gitignore.export(argsMulti.expExportLoc)
        print(f"The data of jobs saves in '{dataPowerJobsName}'.")

        return dataPowerJobs, expPurityList, expEntropyList

    """Other"""
    
    def dataPacking(
        self,
        tags: Union[list[dataTagsAllow], dataTagsAllow],
        items: list[str] = ['purity', 'entropy'],
    ) -> dict:
        ...
        
        if isinstance(tags, list):
            tagsList = tags
        else:
            tagsList = [tags]
        
        for tag in list(tagsList):
            if tag not in self.expsBelong:
                tagsList.remove(tag)
                print(f"'{tag}' does not exist in '.expsBelong'")
            
        dataPackage = {
            tag: self.expsBelong[tag] for tag in tagsList
        }

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
        return f"{self.__name__}"

    def to_dict(self) -> dict:
        return self.__dict__
