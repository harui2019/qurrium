from qiskit import (
    Aer, execute,
    QuantumRegister, ClassicalRegister, QuantumCircuit)
from qiskit.tools import *
from qiskit.visualization import *

from qiskit.providers import Backend
from qiskit.providers.ibmq import IBMQBackend
from qiskit.providers.ibmq.managed import ManagedResults

from qiskit.quantum_info import random_unitary
from qiskit.result import Result

from matplotlib.figure import Figure
import numpy as np
import gc
import warnings
from typing import Union, Optional, Callable, List
from itertools import combinations
from qiskit.visualization.counts_visualization import hamming_distance

from .qurrentV2 import EntropyMeasureV2
# haarMeasure

RXmatrix = np.array([[0, 1], [1, 0]])
RYmatrix = np.array([[0, -1j], [1j, 0]])
RZmatrix = np.array([[1, 0], [0, -1]])


def makeTwoBitStr(num: int, bits: List[str] = ['']) -> List[str]:
    return ((lambda bits: [
        *['0'+item for item in bits], *['1'+item for item in bits]
    ])(makeTwoBitStr(num-1, bits)) if num > 0 else bits)


makeTwoBitStrOneLiner: Callable[[int, List[str]], List[str]] = (
    lambda num, bits=['']: ((lambda bits: [
        *['0'+item for item in bits], *['1'+item for item in bits]]
    )(makeTwoBitStrOneLiner(num-1, bits)) if num > 0 else bits))


# haarMeasureV1
# at Legacy branch `entropymeasurev1`

# haarMeasureV2

class haarMeasureV2(EntropyMeasureV2):
    def initialize(self) -> dict[str: any]:
        """Configuration to Initialize 'haarMeasure'.
        - 
        ```
        self.measureConfig = {
            'name': 'haarMeasure',
            'shortName': 'haar',
            'paramsNum': 3,
            'default': {
                'degree': (
                    self.waves[-1].num_qubits/2 if (self.waves[-1].num_qubits % 2 == 0)
                    else int((self.waves[-1].num_qubits-1)/2+1)),
                'times': 100,
                'purityMethod': 1,
            },
            'hint': {
                'degree': 'degree of freedom of subsystem A.',
                'times': 'number of test to count ensemble average at least 10, default 100.',
                'purityMethod': [
                    '1: ensemble Ave. (default)'
                    '2: standard deviation',
                    '3: no double count ensemble Ave.'],
                'measure': 'number of the qubits which measure.',
            },
            'otherHint': """ """,
        }
        ```

        Returns:
            dict[str: any]: The basic configuration of `haarMeasure`.
        """

        self.measureConfig = {
            'name': 'haarMeasure',
            'shortName': 'haar',
            'paramsNum': 3,
            'default': {
                'degree': (
                    self.waves[self.lastWave].num_qubits/2 if (self.waves[self.lastWave].num_qubits % 2 == 0)
                    else int((self.waves[self.lastWave].num_qubits-1)/2+1)),
                'times': 100,
                'purityMethod': 1,
            },
            'hint': {
                'degree': 'degree of freedom of subsystem A.',
                'times': 'number of test to count ensemble average at least 10, default 100.',
                'purityMethod': [
                    '1: ensemble Ave. (default)'
                    '2: standard deviation',
                    '3: no double count ensemble Ave.'],
                'measure': 'number of the qubits which measure.',
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
        args = self.now
        numQubits = self.waves[args.wave].num_qubits

        qcExpList = []
        for times in range(args.paramsOther['times']):
            qFunc1 = QuantumRegister(numQubits, 'q1')
            cMeas = ClassicalRegister(numQubits, 'c1')
            qcExp = QuantumCircuit(qFunc1, cMeas)

            qcExp.append(self.waveInstruction(
                wave=args.wave,
                runBy=args.runBy,
                backend=args.backend,
            ), [qFunc1[i] for i in range(numQubits)])

            if not isinstance(args.backend, IBMQBackend):
                qcExp.barrier()

            [qcExp.append(random_unitary(2), [i])
                for i in range(numQubits)]

            if not isinstance(args.backend, IBMQBackend):
                qcExp.save_density_matrix()

            [qcExp.measure(qFunc1[i], cMeas[i]) for i in range(numQubits)]

            qcExpList.append(qcExp)

        return qcExpList

    @staticmethod
    def hamming_distance(str1, str2):
        """Calculate the Hamming distance between two bit strings

        From `qiskit.visualization.count_visualization`.

        Args:
            str1 (str): First string.
            str2 (str): Second string.
        Returns:    
            int: Distance between strings.
        Raises:
            VisualizationError: Strings not same length
        """
        if len(str1) != len(str2):
            raise VisualizationError("Strings not same length.")
        return sum(s1 != s2 for s1, s2 in zip(str1, str2))

    @staticmethod
    def ensembleCell(
        sAi: str,
        sAiMeas: int,
        sAj: str,
        sAjMeas: int,
        aNum: int,
        shots: int,
    ) -> float:
        """Calculate the value of two counts from qubits in ensemble average.

        - about `diff = hamming_distance(sAi, sAj)`:

            It is `hamming_distance` from `qiskit.visualization.count_visualization`.
            Due to frequently update of Qiskit and it's a simple function,
            I decide not to use source code instead of calling from `qiskit`.

        Args:
            sAi (str): First count's qubits arrange.
            sAiMeas (int): First count.
            sAj (str): Second count's qubits arrange.
            sAjMeas (int): Second count.
            aNum (int): Degree of freedom.
            shots (int): Shots of executation.

        Returns:
            float: the value of two counts from qubits in ensemble average.

        """
        diff = sum(s1 != s2 for s1, s2 in zip(sAi, sAj))
        tmp = (
            np.float_power(2, aNum)*np.float_power(-2, -diff)
        )*(
            (sAiMeas/shots)*(sAjMeas/shots)
        )
        return tmp

    @staticmethod
    def densityToBloch(
        rho: np.array
    ) -> List[float]:
        """Convert a density matrix to a Bloch vector.

        Args:
            rho (np.array): The density matrix.

        Returns:
            List[float]: The bloch vector.
        """

        ax = np.trace(np.dot(rho, RXmatrix)).real
        ay = np.trace(np.dot(rho, RYmatrix)).real
        az = np.trace(np.dot(rho, RZmatrix)).real
        return [ax, ay, az]

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
            resultIdxList = [i for i in range(paramsOther['times'])]
        elif isinstance(resultIdxList, list):
            if len(resultIdxList) > 1:
                ...
            else:
                raise ValueError(
                    "The element number of 'resultIdxList' needs to be more than 1 for 'haarMeasure'.")
        else:
            raise ValueError("'resultIdxList' needs to be 'list'.")

        counts = [result.get_counts(i) for i in resultIdxList]
        purity = -100
        entropy = -100
        purityCellList = []

        for t in resultIdxList:
            allMeas = result.get_counts(t)
            allMeasUnderDegree = dict.fromkeys(
                [k[:aNum] for k in allMeas], 0)
            for kMeas in list(allMeas):
                allMeasUnderDegree[kMeas[:aNum]] += allMeas[kMeas]
            # print("before: ", allMeas)
            # print("after : ", allMeasUnderDegree)
            purityCell = 0

            # if paramsOther['purityMethod'] == 3:

                # for (sAi, sAiMeas), (sAj, sAjMeas) in list(
                #     combinations(allMeasUnderDegree.items(), 2)
                # ):
                #     purityCell += cls.ensembleCell(
                #         sAi, sAiMeas, sAj, sAjMeas, aNum, shots)
                # for sAi, sAiMeas in allMeasUnderDegree.items():
                #     purityCell += cls.ensembleCell(
                #         sAi, sAiMeas, sAi, sAiMeas, aNum, shots)

            if paramsOther['purityMethod'] == 2:

                purityCell = 0
                isZeroInclude = '0' in allMeas
                isOneInclude = '1' in allMeas
                if isZeroInclude and isOneInclude:
                    purityCell = (allMeas['0'] - allMeas['1'])/shots
                elif isZeroInclude:
                    purityCell = allMeas['0']/shots
                elif isOneInclude:
                    purityCell = allMeas['1']/shots
                else:
                    purity = 0
                    raise Warning(
                        "Expected '0' and '1', but there is no such keys")

            else:
                for sAi, sAiMeas in allMeasUnderDegree.items():
                    for sAj, sAjMeas in allMeasUnderDegree.items():
                        purityCell += cls.ensembleCell(
                            sAi, sAiMeas, sAj, sAjMeas, aNum, shots)

            purityCellList.append(purityCell)

        if paramsOther['purityMethod'] == 2:
            tmp = np.sqrt(3)*np.std(purityCellList)
            purity = (1+tmp**2)/2
            print("method:", "standard deviation")

        elif paramsOther['purityMethod'] == 3:
            purity = np.mean(purityCellList)
            print("method:", "no double count ensemble ave.")

        else:
            purity = np.mean(purityCellList)
            print("method:", "double count ensemble ave.")

        entropy = -np.log2(purity)

        return counts, purity, entropy
