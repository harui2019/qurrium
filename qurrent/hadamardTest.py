from qiskit import (
    Aer, execute,
    QuantumRegister, ClassicalRegister, QuantumCircuit)
from qiskit.tools import *
from qiskit.visualization import *

from qiskit.providers import Backend
from qiskit.providers.ibmq.managed import ManagedResults

from qiskit.quantum_info import random_unitary
from qiskit.result import Result

from matplotlib.figure import Figure
import numpy as np
import gc
import warnings
from typing import Union, Optional, List

from .qurrent import EntropyMeasureV2
from .qurrentV1 import EntropyMeasureV1

# hadamardTestV1


class hadamardTest(EntropyMeasureV1):
    def initialize(self) -> None:
        """Initialize hadamardTest
        """

        self.measurementName = 'hadamardTest'
        self.shortName = 'hadamard'
        self.requiredParaNum = 1
        self.defaultPara = [self.numQubits]
        self.defaultParaKey = ['degree']
        self.requiredParaNote = ['degree of freedom of subsystem A']

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

        qAnc = QuantumRegister(1, 'ancilla')
        qFunc1 = QuantumRegister(self.numQubits, 'q1')
        qFunc2 = QuantumRegister(self.numQubits, 'q2')
        cMeas = ClassicalRegister(1, 'c')
        qcExp = QuantumCircuit(qAnc, qFunc1, qFunc2, cMeas)

        runByResult = self.waveCircuitGated if runBy == "gate" else self.waveCircuitOperator
        qcExp.append(runByResult, [qFunc1[i] for i in range(self.numQubits)])
        qcExp.append(runByResult, [qFunc2[i] for i in range(self.numQubits)])

        qcExp.barrier()
        qcExp.h(qAnc)
        if aNum > 0:
            [qcExp.cswap(qAnc[0], qFunc1[i], qFunc2[i]) for i in range(aNum)]
        qcExp.h(qAnc)
        qcExp.measure(qAnc, cMeas)

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

        AncMeas = self.base[tgtExpId]['result'].get_counts()
        indexOfCounts = list(AncMeas.keys())
        isZeroInclude = '0' in indexOfCounts
        isOneInclude = '1' in indexOfCounts
        shots = sum(AncMeas.values())
        purity = 0  # purity
        if isZeroInclude and isOneInclude:
            purity = (AncMeas['0'] - AncMeas['1'])/shots
        elif isZeroInclude:
            purity = AncMeas['0']/shots
        elif isOneInclude:
            purity = AncMeas['1']/shots
        else:
            purity = None
            raise Warning("Expected '0' and '1', but there is no such keys")

        counts = AncMeas
        entropy = -np.log2(purity)

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


# hadamardTestV2

class hadamardTestV2(EntropyMeasureV2):
    def initialize(self) -> dict[str: any]:
        """Configuration to Initialize 'hadamardTest'.

        Returns:
            dict[str: any]: The basic configuration of `hadamardTest`.
        """

        self.measureConfig = {
            'name': 'hadamardTest',
            'shortName': 'hadamard',
            'paramsNum': 1,
            'default': {
                'degree': (
                    self.waves[self.lastWave].num_qubits/2 if (self.waves[self.lastWave].num_qubits % 2 == 0)
                    else int((self.waves[self.lastWave].num_qubits-1)/2+1))
            },
            'hint': {
                'degree': 'degree of freedom of subsystem A.',
            },
            'otherHint': """ """,
        }

        self.paramsKey = []

        return self.measureConfig

    def circuitMethod(
        self,
    ) -> Union[QuantumCircuit, list[QuantumCircuit]]:
        """The method to construct circuit.

        Returns:
            Union[QuantumCircuit, list[QuantumCircuit]]: 
                The quantum circuit of experiment.
        """
        ArgsNow = self.now
        numQubits = self.waves[ArgsNow.wave].num_qubits

        qAnc = QuantumRegister(1, 'ancilla')
        qFunc1 = QuantumRegister(numQubits, 'q1')
        qFunc2 = QuantumRegister(numQubits, 'q2')
        cMeas = ClassicalRegister(1, 'c')
        qcExp = QuantumCircuit(qAnc, qFunc1, qFunc2, cMeas)

        qcExp.append(self.waveInstruction(
            wave=ArgsNow.wave,
            runBy=ArgsNow.runBy,
            backend=ArgsNow.backend,
        ), [qFunc1[i] for i in range(numQubits)])
        qcExp.append(self.waveInstruction(
            wave=ArgsNow.wave,
            runBy=ArgsNow.runBy,
            backend=ArgsNow.backend,
        ), [qFunc2[i] for i in range(numQubits)])

        qcExp.barrier()
        qcExp.h(qAnc)
        if ArgsNow.aNum > 0:
            [qcExp.cswap(qAnc[0], qFunc1[i], qFunc2[i])
                for i in range(ArgsNow.aNum)]
        qcExp.h(qAnc)
        qcExp.measure(qAnc, cMeas)

        return qcExp

    @classmethod
    def purityMethod(
        cls,
        aNum: int,
        paramsOther: dict[str: int],
        shots: int,
        result: Union[Result, ManagedResults],
        resultIdxList: Optional[list[int]] = None,
    ) -> tuple[dict[str, float], float, float]:
        """Computing Purity.

        ```
        paramsOther: {
            'times': 100,
            'purityMethod': 1,
        }
        ```

        Returns:
            tuple[dict[str, float], float, float]: 
                Counts, purity, entropy of experiment.
        """

        if resultIdxList == None:
            resultIdxList = [0]
        elif isinstance(resultIdxList, list):
            if len(resultIdxList) == 1:
                ...
            else:
                raise ValueError(
                    "The element number of 'resultIdxList' needs to 1 for 'hadamardTest'.")
        else:
            raise ValueError("'resultIdxList' needs to be 'list'.")

        counts = [result.get_counts(i) for i in resultIdxList]
        onlyCount = counts[0]
        purity = -100
        entropy = -100

        isZeroInclude = '0' in onlyCount
        isOneInclude = '1' in onlyCount
        if isZeroInclude and isOneInclude:
            purity = (onlyCount['0'] - onlyCount['1'])/shots
        elif isZeroInclude:
            purity = onlyCount['0']/shots
        elif isOneInclude:
            purity = onlyCount['1']/shots
        else:
            purity = None
            raise Warning("Expected '0' and '1', but there is no such keys")

        entropy = -np.log2(purity)

        return onlyCount, purity, entropy
