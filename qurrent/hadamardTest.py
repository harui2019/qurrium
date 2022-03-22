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

# hadamardTestV1
# at Legacy branch `entropymeasurev1`

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
