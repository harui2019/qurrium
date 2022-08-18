from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit.providers.ibmq.managed import ManagedResults, IBMQManagedResultDataNotAvailable
from qiskit.quantum_info import random_unitary
from qiskit.result import Result

import numpy as np
import warnings
from typing import Union, Optional, NamedTuple
import time

from .qurrech import EchoListen
from ..qurrium import haarBase
# EchoListen V0.3.0 - Measuring Loschmidt Echo - Qurrech


class haarMeasure(EchoListen, haarBase):
    """haarMeasure V0.3.0 of qurrech

    - Reference:
        - Used in:
            Statistical correlations between locally randomized measurements: A toolbox for probing entanglement in many-body quantum states - A. Elben, B. Vermersch, C. F. Roos, and P. Zoller, [PhysRevA.99.052323](https://doi.org/10.1103/PhysRevA.99.052323)

        - `bibtex`:

```bibtex
@article{PhysRevA.99.052323,
    title = {Statistical correlations between locally randomized measurements: A toolbox for probing entanglement in many-body quantum states},
    author = {Elben, A. and Vermersch, B. and Roos, C. F. and Zoller, P.},
    journal = {Phys. Rev. A},
    volume = {99},
    issue = {5},
    pages = {052323},
    numpages = {12},
    year = {2019},
    month = {May},
    publisher = {American Physical Society},
    doi = {10.1103/PhysRevA.99.052323},
    url = {https://link.aps.org/doi/10.1103/PhysRevA.99.052323}
}
```
    """

    """ Configuration """
    class argsCore(NamedTuple):
        expsName: str = 'exps',
        wave1: Union[QuantumCircuit, any, None] = None,
        wave2: Union[QuantumCircuit, any, None] = None,
        times: int = 100,

    # Initialize
    def initialize(self) -> dict[str, any]:
        """Configuration to Initialize haarMeasure.

        Returns:
            dict[str, any]: The basic configuration of `haarMeasure`.
        """

        self._expsConfig = self.expsConfig(
            name="qurrechConfig",
        )
        self._expsBase = self.expsBase(
            name="qurrechBase",
            defaultArg={
                # Reault of experiment.
                'echo': -100,
            },
        )
        self._expsHint = self.expsHint(
            name='qurrechBaseHint',
            hintContext={
                'echo': 'The Loschmidt Echo.',
            },
        )
        self._expsMultiConfig = self.expsConfigMulti(
            name="qurrentConfigMulti",
        )
        self.shortName = 'qurrech.haar'
        self.__name__ = 'qurrech.haarMeasure'

        return self._expsConfig, self._expsBase

    """Arguments and Parameters control"""

    def paramsControlCore(
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
            tuple[str, dict[str, any]]: Current `expID` and arguments.
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
            'expsName': f"w1={wave1}-w2={wave2}-at={times}.{self.shortName}",
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

        ABegin = time.time()
        print(f"| Build circuit A: {argsNow.wave1}", end="\r")
        for i in range(argsNow.times):
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
            print(
                f"| Build circuit A: {argsNow.wave1}" +
                f" - {i+1}/{argsNow.times} - {round(time.time() - ABegin, 3)}s.", end="\r")
        print(
            f"| Circuit completed A: {argsNow.wave1}" +
            f" - {i+1}/{argsNow.times} - {round(time.time() - ABegin, 3)}s." +
            " "*30)

        BBegin = time.time()
        print(f"| Build circuit B: {argsNow.wave2}", end="\r")
        for i in range(argsNow.times):
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
            print(
                f"| Build circuit B: {argsNow.wave2}" +
                f" - {i+1}/{argsNow.times} - {round(time.time() - BBegin, 3)}s.", end="\r")
        print(
            f"| Circuit completed B: {argsNow.wave2}" +
            f" - {i+1}/{argsNow.times} - {round(time.time() - BBegin, 3)}s." +
            " "*30)

        self.exps[self.IDNow]['sideProduct']['randomized'] = {
            i: [self.qubitOpToPauliCoeff(unitaryList[i][j])
                for j in range(numQubits)]
            for i in range(argsNow.times)}

        return qcList

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

        counts = []
        counts01, counts02 = [], []
        echo = -100
        echoCellList = []

        Begin = time.time()
        print(f"| Calculating overlap ...", end="\r")
        for i in range(times):
            echoCell = 0
            t1 = resultIdxList[i]
            t2 = resultIdxList[i+times]
            print(
                f"| Calculating overlap {t1} and {t2}" +
                f" - {i+1}/{times} - {round(time.time() - Begin, 3)}s.", end="\r")

            try:
                allMeas1 = result.get_counts(t1)
                allMeas2 = result.get_counts(t2)
                counts01.append(allMeas1)
                counts02.append(allMeas2)
            except IBMQManagedResultDataNotAvailable as err:
                counts01.append(None)
                counts02.append(None)
                print("| Failed Job result skip, index:", t1, err)
                continue

            numAllMeas1 = len(allMeas1)
            numAllMeas2 = len(allMeas2)
            aNum = len(list(allMeas1.keys())[0])

            print(
                f"| Calculating overlap {t1} and {t2} " +
                f"by summarize {numAllMeas1*numAllMeas2} values - {i+1}/{times}" +
                f" - {round(time.time() - Begin, 3)}s.", end="\r")
            for sAi, sAiMeas in allMeas1.items():
                for sAj, sAjMeas in allMeas2.items():
                    echoCell += cls.ensembleCell(
                        sAi, sAiMeas, sAj, sAjMeas, aNum, shots)

            echoCellList.append(echoCell)
            print(
                f"| Calculating overlap end - {i+1}/{times}" +
                f" - {round(time.time() - Begin, 3)}s." +
                " "*30, end="\r")
        print(
            f"| Calculating overlap end - {i+1}/{times}" +
            f" - {round(time.time() - Begin, 3)}s.")

        echo = np.mean(echoCellList)
        counts = counts01 + counts02

        quantity = {
            'echo': echo,
            '_echoCellList': echoCellList,
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
