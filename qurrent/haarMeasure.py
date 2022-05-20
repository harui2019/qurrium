from qiskit import (
    QuantumRegister, ClassicalRegister, QuantumCircuit)
from qiskit.providers.ibmq.managed import ManagedResults
from qiskit.visualization import *
from qiskit.visualization.counts_visualization import hamming_distance
from qiskit.quantum_info import random_unitary
from qiskit.result import Result

import numpy as np
import warnings
from typing import Union, Optional, Callable, List, NamedTuple
import time

from .qurrent import EntropyMeasureV3
from ..tool import Configuration
# EntropyMeasure V0.3.0 - Measuring Renyi Entropy - Qurrent

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


class haarMeasureV3(EntropyMeasureV3):
    """haarMeasure V0.3.0 of qurrech
    """

    """ Configuration """

    class argdictCore(NamedTuple):
        expsName: str = 'exps',
        wave: Union[QuantumCircuit, any, None] = None,
        degree: Optional[int] = None,
        times: int = 100,

    # Initialize
    def initialize(self) -> dict[str: any]:
        """Configuration to Initialize haarMeasure.

        Returns:
            dict[str: any]: The basic configuration of `haarMeasure`.
        """

        self._expsConfig = self.expsConfig(
            name="qurrentConfig",
        )
        self._expsBase = self.expsBase(
            name="qurrentBase",
            defaultArg={
                # Reault of experiment.
                'entropy': -100,
                'purity': -100,
            },
        )
        self._expsHint = self.expsHint(
            name='qurrechBaseHint',
            hintContext={
                'entropy': 'The Renyi Entropy.',
                'purity': '',
            },
        )
        self._expsMultiConfig = self.expsConfigMulti(
            name="qurrentConfigMulti",
        )
        self.shortName = 'qurrentV3.haar'
        self.__name__ = 'qurrentV3.haar'

        return self._expsConfig, self._expsBase

    """Arguments and Parameters control"""

    def paramsControlMain(
        self,
        expsName: str = 'exps',
        wave: Union[QuantumCircuit, any, None] = None,
        degree: Optional[int] = None,
        times: int = 100,
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

            degree (Optional[int], optional): 
                The degree of freedom.
                If input is `None`, 
                then use the number of half qubits for even number of qubits, 
                or (the number of qubits + 1)/2 for odd number of qubits.
                If input is illegal, then raise ValueError.
                Defaults to None.

            times (int, optional): 
                The number of test to count ensemble average.
                Defaults to `100`.

            expsName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            otherArgs (any):
                Other arguments.

        Raises:
            KeyError: Given `expID` does not exist.
            TypeError: When parameters are not all to be `int`.
            KeyError: The given parameters lost degree of freedom.".

        Returns:
            tuple[str, dict[str: any]]: Current `expID` and arguments.
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

        # degree
        numQubits = self.waves[wave].num_qubits
        if degree > numQubits:
            raise ValueError(
                f"The subsystem A includes {degree} qubits beyond {numQubits} which the wave function has.")
        elif degree < 0:
            raise ValueError(
                f"The number of qubits of subsystem A has to be natural number.")

        # times
        if not isinstance(times, int):
            raise ValueError("'times' must be an 'int'.")
        elif times <= 0:
            raise ValueError("'times' must be larger than 0.")

        return {
            'wave': wave,
            'degree': degree,
            'times': times,
            'numQubit': numQubits,
            'expsName': f"{expsName}.{wave}-deg={degree}-at{times}.{self.__name__}",
            **otherArgs,
        }

    """ Main Process: Circuit"""

    def circuitMethod(
        self,
    ) -> Union[QuantumCircuit, list[QuantumCircuit]]:
        """The method to construct circuit.
        Where should be overwritten by each construction of new measurement.

        Returns:
            Union[QuantumCircuit, list[QuantumCircuit]]: 
                The quantum circuit of experiment.
        """
        argsNow: super().argdictNow = self.now
        numQubits = self.waves[argsNow.wave].num_qubits

        qcList = []
        unitaryList = [
            [random_unitary(2) for _ in range(numQubits)]
            for i in range(argsNow.times)]

        ABegin = time.time()
        print(f"| Build circuit: {argsNow.wave}", end="\r")
        for i in range(argsNow.times):
            qFunc1 = QuantumRegister(numQubits, 'q1')
            cMeas1 = ClassicalRegister(numQubits, 'c1')
            qcExp1 = QuantumCircuit(qFunc1, cMeas1)

            qcExp1.append(self.waveInstruction(
                wave=argsNow.wave,
                runBy=argsNow.runBy,
                backend=argsNow.backend,
            ), [qFunc1[i] for i in range(numQubits)])

            qcExp1.barrier()
            for j in range(numQubits):
                qcExp1.append(unitaryList[i][j], [j])
            for j in range(numQubits):
                qcExp1.measure(qFunc1[j], cMeas1[j])

            qcList.append(qcExp1)
            print(
                f"| Build circuit: {argsNow.wave}" +
                f" - {i+1}/{argsNow.times} - {round(time.time() - ABegin, 3)}s.", end="\r")
        print(
            f"| Circuit completed: {argsNow.wave}" +
            f" - {i+1}/{argsNow.times} - {round(time.time() - ABegin, 3)}s." +
            " "*30)

        return qcList

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
    def quantity(
        cls,
        shots: int,
        result: Union[Result, ManagedResults],
        resultIdxList: Optional[list[int]] = None,
        times: int = 0,
        degree: int = None,
        **otherArgs,
    ) -> tuple[dict, dict]:
        """Computing specific quantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            tuple[dict, dict]:
                Counts, purity, entropy of experiment.
        """
        if resultIdxList == None:
            resultIdxList = [i for i in range(times)]
        elif isinstance(resultIdxList, list):
            if len(resultIdxList) > 1:
                ...
            elif len(resultIdxList) != times:
                raise ValueError(
                    f"The element number of 'resultIdxList': {len(resultIdxList)} is different with 'times': {times}.")
            else:
                raise ValueError(
                    f"The element number of 'resultIdxList': {len(resultIdxList)} needs to be more than 1 for 'haarMeasure'.")
        else:
            raise ValueError("'resultIdxList' needs to be 'list'.")

        counts = [result.get_counts(i) for i in resultIdxList]
        purity = -100
        entropy = -100
        purityCellList = []

        Begin = time.time()
        print(f"| Calculating overlap ...", end="\r")
        for i in range(times):
            purityCell = 0
            t1 = resultIdxList[i]
            print(
                f"| Calculating overlap {t1} and {t1}" +
                f" - {i+1}/{times} - {round(time.time() - Begin, 3)}s.", end="\r")
            allMeas1 = result.get_counts(t1)

            allMeasUnderDegree = dict.fromkeys(
                [k[:degree] for k in allMeas1], 0)
            for kMeas in list(allMeas1):
                allMeasUnderDegree[kMeas[:degree]] += allMeas1[kMeas]
            numAllMeasUnderDegree = len(allMeasUnderDegree)

            print(
                f"| Calculating overlap {t1} and {t1} " +
                f"by summarize {numAllMeasUnderDegree**2} values - {i+1}/{times}" +
                f" - {round(time.time() - Begin, 3)}s.", end="\r")
            for sAi, sAiMeas in allMeasUnderDegree.items():
                for sAj, sAjMeas in allMeasUnderDegree.items():
                    purityCell += cls.ensembleCell(
                        sAi, sAiMeas, sAj, sAjMeas, degree, shots)

            purityCellList.append(purityCell)
            print(
                f"| Calculating overlap end - {i+1}/{times}" +
                f" - {round(time.time() - Begin, 3)}s." +
                " "*30, end="\r")
        print(
            f"| Calculating overlap end - {i+1}/{times}" +
            f" - {round(time.time() - Begin, 3)}s.")

        purity = np.mean(purityCellList)
        entropy = -np.log2(purity)
        quantity = {
            'purity': purity,
            'entropy': entropy,
        }
        return counts, quantity

    """ Main Process: Main Control"""

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        degree: Optional[int] = None,
        times: int = 100,
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
            degree=degree,
            times=times,
            expsName=expsName,
            **otherArgs,
        )
