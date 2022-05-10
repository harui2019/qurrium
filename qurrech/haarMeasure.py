from qiskit import (
    QuantumRegister, ClassicalRegister, QuantumCircuit)
from qiskit.providers.ibmq.managed import ManagedResults
from qiskit.visualization import *

from qiskit.quantum_info import random_unitary
from qiskit.result import Result

import numpy as np
import warnings
from typing import Union, Optional, Callable, List
from qiskit.visualization.counts_visualization import hamming_distance

from tqdm import trange, tqdm

from .qurrech import EchoListen
from ..qurry import (
    expsConfig,
    expsBase,
    expsConfigMulti,
    expsHint
)
# EchoListen V0.3.0 - Measuring Loschmidt Echo - Qurrech

_expsConfig = expsConfig(
    name="qurrechConfig",
    defaultArg={
        # Variants of experiment.
        'wave1': None,
        'wave2': None,
        'times': 100,
    },
)

_expsBase = expsBase(
    name="qurrechBase",
    expsConfig=_expsConfig,
    defaultArg={
        # Reault of experiment.
        'echo': -100,
    },
)

_expsMultiConfig = expsConfigMulti(
    name="qurrechConfigMulti",
    expsConfig=_expsConfig,
    defaultArg={
        # Reault of experiment.
        'echo': -100,
    },
)

_expsHint = expsHint(
    name='qurrechBaseHint',
    expsConfig=_expsBase,
    hintContext={
        'echo': 'The Loschmidt Echo.',
    },
)

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


class haarMeasure(EchoListen):
    """haarMeasure V0.3.0 of qurrech
    """

    # Initialize
    def initialize(self) -> dict[str: any]:
        """Configuration to Initialize haarMeasure.

        Returns:
            dict[str: any]: The basic configuration of `haarMeasure`.
        """

        self._expsConfig = _expsConfig
        self._expsBase = _expsBase
        self._expsHint = _expsHint
        self._expsMultiConfig = _expsMultiConfig
        self.shortName = 'haarMeasure'
        self.__name__ = 'haarMeasure'

        return self._expsConfig, self._expsBase

    """Arguments and Parameters control"""

    def paramsControlMain(
        self,
        expsName: str = 'exps',
        wave1: Union[QuantumCircuit, any, None] = None,
        wave2: Union[QuantumCircuit, any, None] = None,
        times: int = 100,
        **otherArgs: any
    ) -> dict:
        """Handling all arguments and initializing a single experiment.

        Args:
            wave1, wave2 (Union[QuantumCircuit, int, None], optional): 
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
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

        # wave1
        if isinstance(wave1, QuantumCircuit):
            wave1 = self.addWave(wave1)
            print(f"| Add new wave with key: {wave1}")
        elif wave1 == None:
            wave1 = self.lastWave
            print(f"| Autofill will use '.lastWave' as key")
        else:
            try:
                self.waves[wave1]
            except KeyError as e:
                warnings.warn(f"'{e}', use '.lastWave' as key")
                wave1 = self.lastWave

        # wave2
        if isinstance(wave2, QuantumCircuit):
            wave2 = self.addWave(wave2)
            print(f"| Add new wave with key: {wave2}")
        elif wave2 == None:
            wave2 = self.lastWave
            print(f"| Autofill will use '.lastWave' as key")
        else:
            try:
                self.waves[wave2]
            except KeyError as e:
                warnings.warn(f"'{e}', use '.lastWave' as key")
                wave2 = self.lastWave

        # times
        if not isinstance(times, int):
            raise ValueError("'times' must be an 'int'.")
        elif times <= 0:
            raise ValueError("'times' must be larger than 0.")

        return {
            'wave1': wave1,
            'wave2': wave2,
            'times': times,
            'expsName': f"{expsName}.{wave1}-{wave2}at{times}.haar",
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
        argsNow = self.now
        if (self.waves[argsNow.wave1].num_qubits != self.waves[argsNow.wave2].num_qubits):
            raise ValueError(
                "Wave1 and Wave2 must be the same number of qubits.")
        numQubits = self.waves[argsNow.wave1].num_qubits

        qcList = []
        unitaryList = [
            [random_unitary(2) for _ in range(numQubits)]
            for i in range(argsNow.times)]

        progressBarA = trange(
            argsNow.times,
            desc=f"| Build circuit A '{argsNow.wave1}'",
        )
        for i in progressBarA:
            qFunc1 = QuantumRegister(numQubits, 'q1')
            cMeas1 = ClassicalRegister(numQubits, 'c1')
            qcExp1 = QuantumCircuit(qFunc1, cMeas1)

            qcExp1.append(self.waveInstruction(
                wave=argsNow.wave1,
                runBy=argsNow.runBy,
                backend=argsNow.backend,
            ), [qFunc1[i] for i in range(numQubits)])

            qcExp1.barrier()
            for j in range(numQubits):
                qcExp1.append(unitaryList[i][j], [j])
            for j in range(numQubits):
                qcExp1.measure(qFunc1[j], cMeas1[j])

            qcList.append(qcExp1)
            progressBarA.set_description(
                f"| Build circuit A '{argsNow.wave1}'")

        progressBarB = trange(
            argsNow.times,
            desc=f"| Build circuit B '{argsNow.wave2}'",
        )
        for i in progressBarB:
            qFunc2 = QuantumRegister(numQubits, 'q1')
            cMeas2 = ClassicalRegister(numQubits, 'c1')
            qcExp2 = QuantumCircuit(qFunc2, cMeas2)

            qcExp2.append(self.waveInstruction(
                wave=argsNow.wave2,
                runBy=argsNow.runBy,
                backend=argsNow.backend,
            ), [qFunc2[i] for i in range(numQubits)])

            qcExp2.barrier()
            for j in range(numQubits):
                qcExp2.append(unitaryList[i][j], [j])
            for j in range(numQubits):
                qcExp2.measure(qFunc2[j], cMeas2[j])

            qcList.append(qcExp2)
            progressBarB.set_description(
                f"| Build circuit B '{argsNow.wave2}'")

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
        **otherArgs,
    ) -> tuple[dict, dict]:
        """Computing specific quantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            tuple[dict, dict]:
                Counts, purity, entropy of experiment.
        """
        if resultIdxList == None:
            resultIdxList = [i for i in range(times*2)]
        elif isinstance(resultIdxList, list):
            if len(resultIdxList) > 1:
                ...
            elif len(resultIdxList) != times*2:
                raise ValueError(
                    f"The element number of 'resultIdxList': {len(resultIdxList)} is different with 'times x 2': {times*2}.")
            else:
                raise ValueError(
                    f"The element number of 'resultIdxList': {len(resultIdxList)} needs to be more than 1 for 'haarMeasure'.")
        else:
            raise ValueError("'resultIdxList' needs to be 'list'.")

        counts = [result.get_counts(i) for i in resultIdxList]
        echo = -100
        echoCellList = []

        progressBarOverlap = trange(
            times,
            desc=f"| Calculating overlap ...",
        )
        for i in progressBarOverlap:
            echoCell = 0
            t1 = resultIdxList[i]
            t2 = resultIdxList[i+times]
            progressBarOverlap.set_description(
                f"| Calculating overlap {t1} and {t2}")
            allMeas1 = result.get_counts(t1)
            allMeas2 = result.get_counts(t2)
            numAllMeas1 = len(allMeas1)
            numAllMeas2 = len(allMeas2)
            aNum = len(list(allMeas1.keys())[0])

            progressBarOverlap.set_description(
                f"| Calculating overlap {t1} and {t2} by summarize {numAllMeas1*numAllMeas2} values.")
            for sAi, sAiMeas in allMeas1.items():
                for sAj, sAjMeas in allMeas2.items():
                    echoCell += cls.ensembleCell(
                        sAi, sAiMeas, sAj, sAjMeas, aNum, shots)

            echoCellList.append(echoCell)
            progressBarOverlap.set_description(
                f"| Calculating overlap end ...")

        echo = np.mean(echoCellList)

        quantity = {
            'echo': echo,
        }
        return counts, quantity

    """ Main Process: Main Control"""

    def measure(
        self,
        wave1: Union[QuantumCircuit, any, None] = None,
        wave2: Union[QuantumCircuit, any, None] = None,
        times: int = 100,
        expsName: str = 'exps',
        **otherArgs: any
    ) -> dict:
        """The measure function which is the customized version of `.output`.

        Args:
            wave (Union[QuantumCircuit, int, None], optional):
            wave1, wave2 (Union[QuantumCircuit, int, None], optional): 
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
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

        Returns:
            dict: The output.
        """
        return self.output(
            wave1=wave1,
            wave2=wave2,
            times=times,
            expsName=expsName,
            **otherArgs,
        )
