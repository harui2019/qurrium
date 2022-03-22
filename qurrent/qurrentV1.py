from qiskit.tools import *
from qiskit.visualization import *
from qiskit.providers.ibmq import IBMQBackend
from qiskit.providers.ibmq.managed import IBMQJobManager
from qiskit import Aer, execute, QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit.quantum_info import Operator, random_unitary
from qiskit.circuit.gate import Gate
from qiskit.providers import Backend
from matplotlib.figure import Figure
import numpy as np
from uuid import uuid4
import gc
import warnings
from typing import Union, Optional, List, Callable, Any, Iterable, Tuple


# EntropyMeasure

class EntropyMeasureV1:
    def initialize(self) -> None:
        """Initialize EntropyMeasure
        """

        self.measurementName = 'EntropyMeasure'
        self.requiredParaNum = 1
        self.defaultPara = [self.numQubits]
        self.defaultParaKey = ['degree']
        self.requiredParaNote = [
            'degree: degree of freedom of subsystem A.',
            '(this class is not yet configured.)'
        ]

    def __init__(
        self,
        waveCircuit: QuantumCircuit = QuantumCircuit(1)
    ) -> None:
        """Initialize Class.

        Args:
            waveCircuit (QuantumCircuit): The wave function will be measured.
        """
        
        warnings.warn(
            "'EntropyMeasureV1' is an early development remain and "+
            "the prototype of the more reliable 'EntropyMeasureV2' before alpha v0.101. "+
            "Althought it still works but we suggest to use 'EntropyMeasureV2' by importting 'EntropyMeasure', "+
            "because 'EntropyMeasure' has been abandoned and will be deprecated anytime.")
    

        self.waveCircuit = waveCircuit
        self.numQubits = waveCircuit.num_qubits
        self.waveCircuitGated = waveCircuit.to_gate()
        self.base = {}
        self.paramsLegacy = {}
        self.current = None

        self.initialize()
        self.aNum = self.defaultPara[0]
        self.paramsOther = self.defaultPara[1:]

    def drawOfWave(
        self,
        figType: str = 'text',
        composeMethod: Optional[str] = None
    ) -> Union[str, Figure]:
        """Draw the circuit of wave function.

        Args:
            figType (Optional[str], optional): Draw quantum circuit by 
                "text", "matplotlib", or "latex". Defaults to 'text'.
            composeMethod (Optional[str], optional): Draw quantum circuit with 
                composed construction. Defaults to "none". Defaults to None.

        Returns:
            Union[str, Figure]: The figure of wave function.
        """
        qDummy = QuantumRegister(self.numQubits, 'q')
        qcDummy = QuantumCircuit(qDummy)

        qcDummy.append(self.waveCircuitGated, [
            qDummy[i] for i in range(self.numQubits)])
        fig = qcDummy.decompose().draw(
            figType) if composeMethod == "decompose" else qcDummy.draw(figType)
        self.figOfWave = fig

        return fig

    def waveOperator(self) -> Operator:
        """Export wave functin as operator.

        Returns:
            Operator: The operator of wave function.
        """
        self.waveCircuitOperator = Operator(self.waveCircuit)
        return self.waveCircuitOperator

    def waveGate(self) -> Gate:
        """Export wave functin as quantum circuit gate.

        Returns:
            Gate: The gate of wave function.
        """
        return self.waveCircuitGated

    def _aChecker(
        self,
        a: int
    ) -> Exception:
        """[summary]

        Args:
            a (int): The degree of freedom.

        Raises:
            IndexError: Raise when the degree of freedom is out of the number of qubits.
            ValueError: Raise when the degree of freedom is not a nature number.

        Returns:
            Exception: The Error from the value of the degree of freedom.
        """
        if a > self.numQubits:
            raise IndexError(
                f"The subsystem A includes {a} qubits beyond {self.numQubits} which the wave function has.")
        elif a < 0:
            raise ValueError(
                f"The number of qubits of subsystem A has to be natural number.")

    def _helpPrototype(self) -> None:
        """Help prototype.
        """
        print(
            f"There is the list of required parameters '{self.requiredParaNote}'")
        print(f"requiredParaNum:  {self.requiredParaNum:}")
        print(f"defaultParaKey:  {self.defaultParaKey:}")
        print(f"defaultPara:  {self.defaultPara:}")

    def help(self, otherHint: str = "") -> None:
        """Help.

        Args:
            otherHint (str, optional): Hint will be printed. Defaults to "".
        """
        self._helpPrototype()
        print(f"{otherHint}")

    def paramsControl(
        self,
        params: Union[dict[int], List[int], int, None] = None,
        expIdRule: Union[bool, str] = True,
        unChooseHint: str = (
            "No specific number of freedom degrees, out of the number of qubits," +
            f"or unrecognized parameters, using the number of qubits as default."
        )
    ) -> Tuple[bool, int, List[int]]:
        """ From parameters list isolated the degree of freedom and
            other parameters.

        Args:
            params (Union[dict[int], List[int], int, None], optional): 
                Parameters of experiment. Defaults to None.
            expIdRule (Union[bool, str]): Decide whether generate new id to initializw new 
                experiment or continue current experiment, True for create new id, False 
                for continuing current experiment, if self.current == None will create new
                id automatically, giving a key which exists in self.base will 
                switch to this experiment to operate it. Default to False.
            unChooseHint (str, optional): Hint when program decides to use 
                default parameters.  Defaults to ( "No specific number of freedom 
                degrees, out of the number of qubits," + f"or unrecognized parameters, 
                using the number of qubits as default." ).

        Raises:
            TypeError: When parameters are not all to be 'int'.
            KeyError: CRITICAL ERROR OF MEASUREMENT.

        Returns:
            Tuple[bool, int, List[int]]: Experiment id, degree of freedom ,
                & other parameters.
        """

        if type(params) == int:
            self._aChecker(params)
            self.aNum, self.paramsOther = params, self.defaultPara[1:]

        elif type(params) == list:
            for aItem in params:
                if type(aItem) != int:
                    raise TypeError(
                        f"Multiple 'a' configuration has to be 'int'," +
                        f" but we got '{type(aItem)}' at '{params.index(aItem)}.'"
                    )
            aNum, paramsOther = params[0], params[1:]
            if len(params) < self.requiredParaNum:
                print(
                    f"Require '{self.requiredParaNum}' but got {len(params)}," +
                    " auto fill by default params, for more info using '.help()'.")
                paramsOther = [*paramsOther, *self.defaultPara[len(params):]]
            self._aChecker(aNum)
            self.aNum, self.paramsOther = aNum, paramsOther

        elif type(params) == dict:
            if not 'degree' in self.defaultParaKey:
                raise KeyError(
                    "This measurement doesn't require degree of freedom" +
                    "Please check 'self.defaultParaKey' of this class."
                )
            paramsClone = params.copy()
            targetKeys = list(params.keys())
            for k in self.defaultParaKey:
                if not k in targetKeys:
                    paramsClone[k] = self.defaultPara[k]
                    print(
                        f"{k} is not in configuration, auto fill by default params.")

            self.aNum, self.paramsOther = paramsClone['degree'], [
                paramsClone[aItemKey] for aItemKey in self.defaultParaKey[1:]]

        else:
            self.help()
            self.aNum, self.paramsOther = self.numQubits, self.defaultPara[1:]

        if not expIdRule:
            self.current = str(uuid4())
        elif expIdRule == 'dummy':
            ...
        elif self.current == None:
            self.current = str(uuid4())
            print("Set key:", self.current)
        elif expIdRule in self.base.keys():
            self.current = expIdRule
        else:
            ...

        print(self.aNum, self.paramsOther, expIdRule)
        self.paramsLegacy[self.current] = {
            "aNum": self.aNum,
            "params": [self.aNum, *self.paramsOther],
        }

        return self.aNum, self.paramsOther, self.current

    def drawCircuit(
        self,
        expId: Optional[str],
        params: Union[List[int], int, None] = None,
        figType: Optional[str] = 'text',
        composeMethod: Optional[str] = None
    ) -> Union[str, Figure]:
        """Drawing the circuit figure of the experiment

        Args:
            expId (str): The unique id of experiment, by uuid4.
            figType (Optional[str], optional): Draw quantum circuit by 
                "text", "matplotlib", or "latex". Defaults to 'text'.
            composeMethod (Optional[str], optional): Draw quantum circuit with 
                composed construction. Defaults to "none". Defaults to None.

        Raises:
            KeyError: When 'expId' is not given or not existed.

        Returns:
            Union[str, Figure]: The figure of quantum circuit.
        """

        if expId not in self.base:
            raise KeyError(f"Experiment '{expId}' is not existed.")
        fig = None
        if figType != None:
            qcExp = self.base[expId]['circuit']
            fig = (
                qcExp.decompose().draw(figType) if composeMethod == "decompose"
                else qcExp.draw(figType)
            )
        self.base[expId]['fig'] = fig
        return fig

    def circuitMethod(
        self,
        tgtExpId: str,
        aNum: int,
        paramsOther: list,
        runBy: str = "gate",
    ) -> Union[QuantumCircuit, list[QuantumCircuit]]:
        """The method to construct circuit.

        Args:
            tgtExpId (str): The unique id of experiment, by uuid4.
            aNum (int): Degree of freedom.
            paramsOther (list): Parameters of experiment.
            runBy (str, optional): Construct wave function as initial state 
                by 'Operater' or 'gate. Defaults to "gate".

        Returns:
            Union[QuantumCircuit, list[QuantumCircuit]]: 
                The quantum circuit of experiment.
        """

        qFunc1 = QuantumRegister(self.numQubits, 'q1')
        cMeas = ClassicalRegister(self.numQubits, 'c1')
        qcExp = QuantumCircuit(qFunc1, cMeas)

        runByResult = (
            self.waveCircuitGated if runBy ==
            "gate" else self.waveCircuitOperator)
        qcExp.append(
            runByResult, [qFunc1[i] for i in range(self.numQubits)])

        [qcExp.measure(qFunc1[i], cMeas[i]) for i in range(aNum)]

        print("It's default circuit, the quantum circuit is not yet configured.")

        return qcExp

    def circuitOnly(
        self,
        expId: Optional[str],
        params: Union[List[int], int, None] = None,
        runBy: str = "gate",
        figType: Optional[str] = 'text',
        composeMethod: Optional[str] = None
    ) -> QuantumCircuit:
        """Construct the quantum circuit of experiment.

        Args:
            expId (Optional[str]):  The unique id of experiment, by uuid4.
            params (Union[dict[int], List[int], int, None], optional): 
                Parameters of experiment. Defaults to None.
            runBy (str, optional): Construct wave function as initial state 
                by 'Operater' or 'gate. Defaults to "gate".
            figType (Optional[str], optional): Draw quantum circuit by 
                "text", "matplotlib", or "latex". Defaults to 'text'.
            composeMethod (Optional[str], optional): Draw quantum circuit with 
                composed construction. Defaults to "none". Defaults to None.

        Raises:
            IndexError: Raise when the degree of freedom is out of the number of qubits.
            ValueError: Raise when the degree of freedom is not a nature number.

        Returns:
            QuantumCircuit: The quantum circuit of experiment.
        """

        if runBy != "gate":
            self.waveOperator()

        aNum, paramsOther, tgtExpId = self.paramsControl(params, expId)
        if aNum > self.numQubits:
            raise IndexError(
                f"The subsystem A includes {aNum} qubits beyond the wave function has.")
        elif aNum < 0:
            raise ValueError(
                f"The number of qubits of subsystem A has to be natural number.")

        qcExp: Union[QuantumCircuit, list[QuantumCircuit]] = self.circuitMethod(
            tgtExpId=tgtExpId,
            aNum=aNum,
            paramsOther=paramsOther,
            runBy=runBy,
        )

        self.base[tgtExpId] = {
            'id': tgtExpId,
            'degree': aNum,
            'parameters': [aNum, *paramsOther],
            'circuit': qcExp,
            'result': None,
            'counts': None,
            'purity': None,
            'entropy': None,
        }
        self.drawCircuit(
            expId=tgtExpId,
            params=params,
            figType=figType,
            composeMethod=composeMethod
        )

        return qcExp

    def runMethod(
        self,
        tgtExpId: str,
        aNum: int,
        paramsOther: list,
        shots: int = 1024,
        backend: Backend = Aer.get_backend('qasm_simulator')
    ) -> Union[dict, list[dict]]:
        """The method deals with jobs .

        Args:
            tgtExpId (str): The unique id of experiment, by uuid4.
            aNum (int): Degree of freedom.
            paramsOther (list): Parameters of experiment.
            shots (int, optional): Shots of the job. Defaults to 1024.
            backend (Backend, optional): The quantum backend. Defaults to 
                Aer.get_backend('qasm_simulator').

        Returns:
            Union[dict, list[dict]]: Result of experiment.
        """

        job = execute(
            self.base[tgtExpId]['circuit'],
            backend,
            shots=shots
        )
        result = job.result()

        return result

    def runOnly(
        self,
        expId: Optional[str],
        params: Union[List[int], int, None] = None,
        runBy: str = "gate",
        figType: Optional[str] = 'text',
        composeMethod: Optional[str] = None,
        shots: int = 1024,
        backend: Backend = Aer.get_backend('qasm_simulator')
    ) -> dict:
        """Export the result after running the job.

        Args:
            expId (Optional[str]):  The unique id of experiment, by uuid4.
            params (Union[dict[int], List[int], int, None], optional): 
                Parameters of experiment. Defaults to None.
            runBy (str, optional): Construct wave function as initial state 
                by 'Operater' or 'gate. Defaults to "gate".
            figType (Optional[str], optional): Draw quantum circuit by 
                "text", "matplotlib", or "latex". Defaults to 'text'.
            composeMethod (Optional[str], optional): Draw quantum circuit with 
                composed construction. Defaults to "none". Defaults to None.
            shots (int, optional): Shots of the job. Defaults to 1024.
            backend (Backend): The quantum backend. Defaults to 
                Aer.get_backend('qasm_simulator').

        Returns:
            dict: The result of the job.
        """

        aNum, paramsOther, tgtExpId = self.paramsControl(params, expId)
        self.circuitOnly(
            expId=tgtExpId,
            params=params,
            runBy=runBy,
            figType=figType,
            composeMethod=composeMethod
        )

        result = self.runMethod(
            tgtExpId=tgtExpId,
            aNum=aNum,
            paramsOther=paramsOther,
            shots=shots,
            backend=backend
        )

        self.base[tgtExpId] = {
            **self.base[tgtExpId],
            'result': result,
            'counts': None,
            'purity': None,
            'entropy': None,
        }

        return result

    def purityMethod(
        self,
        aNum: int,
        paramsOther: List[int],
        shots: int,
        tgtExpId: str
    ) -> tuple[dict[str, float], float, float]:
        """Computing Purity.

        Args:
            aNum (int): Degree of Freedom.
            paramsOther (List[int]): Parameters of experiment.
            shots (int): Shots of the job. Defaults to 1024.
            tgtExpId (str): The unique id of experiment, by uuid4.

        Returns:
            tuple[dict[str, float], float, float]: 
                Counts, purity, entropy of experiment.
        """

        counts = self.base[tgtExpId]['result'].get_counts()
        purity = -100
        entropy = -100
        return counts, purity, entropy

    def purityOnly(
        self,
        expId: Optional[str] = None,
        params: Union[List[int], int, None] = None,
        runBy: str = "gate",
        figType: Optional[str] = 'text',
        composeMethod: Optional[str] = None,
        resultKeep: bool = False,
        shots: int = 1024,
        backend: Backend = Aer.get_backend('qasm_simulator')
    ) -> float:
        """Export the result which completed calculating purity.

        Args:
            expId (Optional[str]): The unique id of experiment, by uuid4.
            params (Union[dict[int], List[int], int, None], optional): 
                Parameters of experiment. Defaults to None.
            runBy (str, optional): Construct wave function as initial state 
                by 'Operater' or 'gate. Defaults to "gate".
            figType (Optional[str], optional): Draw quantum circuit by 
                "text", "matplotlib", or "latex". Defaults to 'text'.
            composeMethod (Optional[str], optional): Draw quantum circuit with 
                composed construction. Defaults to "none". Defaults to None.
            resultKeep (bool): Does keep the result in 'base', it will decide 
                how many memory need to allocate.
            shots (int, optional): Shots of the job. Defaults to 1024.
            backend (Backend): The quantum backend. Defaults to 
                Aer.get_backend('qasm_simulator').


        Returns:
            float: the purity.
        """

        aNum, paramsOther, tgtExpId = self.paramsControl(params, expId)
        self.runOnly(
            expId=tgtExpId,
            params=params,
            runBy=runBy,
            figType=figType,
            composeMethod=composeMethod,
            shots=shots,
            backend=backend
        )

        counts, purity, entropy = self.purityMethod(
            aNum, paramsOther, shots, tgtExpId
        )

        if resultKeep:
            warnings.warn(
                "Result will keep, but it may cause memory overallocated.")
        else:
            print("Entropy and Purity are figured out, result will clear.")
            del self.base[tgtExpId]['result']

        self.base[tgtExpId] = {
            **self.base[tgtExpId],
            'counts': counts,
            'purity': purity,
            'entropy': entropy,
        }
        gc.collect()

        return purity

    def reset(
        self,
        fuse: bool = False
    ) -> None:
        """Reset the measurement and release memory.

        Args:
            fuse (bool, optional): Security for reset. Defaults to False.
        """

        if fuse:
            self.__init__(self.waveCircuit)
            gc.collect()
            print("The measurement has reset and release memory allocating.")
        else:
            print(
                "Fuse breaks to prevent reset accidentally, " +
                "if you are sure about to do it, then use '.reset(True)'."
            )

    def go(
        self,
        expId: Optional[str] = None,
        params: Union[List[int], int, None] = None,
        runBy: str = "gate",
        figType: Optional[str] = 'text',
        composeMethod: Optional[str] = None,
        resultKeep: bool = False,
        shots: int = 1024,
        backend: Backend = Aer.get_backend('qasm_simulator')
    ) -> dict:
        """Export the result which all completed.

        Args:
            expId (Optional[str]):  The unique id of experiment, by uuid4.
            params (Union[dict[int], List[int], int, None], optional): 
                Parameters of experiment. Defaults to None.
            runBy (str, optional): Construct wave function as initial state 
                by 'Operater' or 'gate. Defaults to "gate".
            figType (Optional[str], optional): Draw quantum circuit by 
                "text", "matplotlib", or "latex". Defaults to 'text'.
            composeMethod (Optional[str], optional): Draw quantum circuit with 
                composed construction. Defaults to "none". Defaults to None.
            resultKeep (bool): Does keep the result in 'base', it will decide 
                how many memory need to allocate.
            shots (int, optional): Shots of the job. Defaults to 1024.
            backend (Backend): The quantum backend. Defaults to 
                Aer.get_backend('qasm_simulator').

        Returns:
            dict: the result which all completed.
        """

        aNum, paramsOther, tgtExpId = self.paramsControl(params, expId)
        
        if type(backend) == IBMQBackend:
            ...
            
            
        self.purityOnly(
            expId=tgtExpId,
            params=params,
            runBy=runBy,
            figType=figType,
            composeMethod=composeMethod,
            resultKeep=resultKeep,
            shots=shots,
            backend=backend
        )

        return self.base[tgtExpId]

    def __getattr__(self, __name: str) -> Exception:
        """Get Attribute

        Args:
            __name (str): Attribute

        Raises:
            AttributeError: When the attribute does not exist.

        Returns:
            Exception: No such attribute,.
        """
        raise AttributeError(
            "No such attribute, print it to check attributes.")

    def __repr__(self) -> str:
        return f'{self.measurementName}({self.__dict__})'

    def to_dict(self) -> dict:
        return self.__dict__
