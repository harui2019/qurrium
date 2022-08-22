from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit.result import Result
from qiskit.quantum_info import random_unitary
from qiskit.providers.ibmq.managed import ManagedResults, IBMQManagedResultDataNotAvailable

import numpy as np
import warnings
import time
from typing import Union, Optional, NamedTuple, Hashable

from ..qurrium import QurryV4, haarBase, qubitSelector, waveSelecter, Counts
from ..mori import defaultConfig

# EchoListen V0.4.0 - Measuring Loschmidt Echo - Qurrech


class EchoHaarMeasureV4(QurryV4, haarBase):
    """HaarMeasure V0.4.0 of qurrech

    - Reference:
        - Used in:
            Statistical correlations between locally randomized measurements: 
            A toolbox for probing entanglement in many-body quantum states - 
            A. Elben, B. Vermersch, C. F. Roos, and P. Zoller, 
            [PhysRevA.99.052323](https://doi.org/10.1103/PhysRevA.99.052323)

        - `bibtex`:

```bibtex
@article{PhysRevA.99.052323,
    title = {Statistical correlations between locally randomized measurements: 
    A toolbox for probing entanglement in many-body quantum states},
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
        expsName: str = None
        wave1: Hashable = None
        wave2: Hashable = None
        degree: tuple[int, int] = None
        times: int = 100
        measure: tuple[int, int] = None
        unitary_set: tuple[int, int] = None

    class expsCore(NamedTuple):
        echo: float
        echoSD: float

    # Initialize
    def initialize(self) -> dict[str, any]:
        """Configuration to Initialize haarMeasure.

        Returns:
            dict[str, any]: The basic configuration of `haarMeasure`.
        """
        self._expsBase = defaultConfig(
            name='QurrechHaarBase',
            default={
                **self.argsMain()._asdict(),
                **self.argsCore()._asdict(),
                **self.expsMain()._asdict(),
            },
        )
        self._expsHint = {
            **{k: f"sample: {v}" for k, v in self._expsBase},
            "_basicHint": "This is a hint of QurryV4.",
        }
        self._expsMultiBase = defaultConfig(
            name='QurrechHaarMultiBase',
            default={
                **self.argsMultiMain()._asdict(),
                **self.expsMultiMain()._asdict(),
            },
        )

        self.shortName = 'qurrech_haar'
        self.__name__ = 'qurrech_haarMeasure'

    def paramsControlCore(
        self,
        expsName: Optional[str] = None,
        wave1: Union[QuantumCircuit, any, None] = None,
        wave2: Union[QuantumCircuit, any, None] = None,
        degree: Union[int, tuple[int, int], None] = None,
        times: int = 100,
        measure: Union[int, tuple[int, int]] = None,
        unitary_set: Union[int, tuple[int, int]] = None,
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

            measure (tuple[int, int], optional):
                The range of the qubits will be measured.

            unitary_set (tuple[int, int], optional):
                The range of the qubits will be setted random unitary.

            otherArgs (any):
                Other arguments.

        Raises:
            KeyError: Given `expID` does not exist.
            TypeError: When parameters are not all to be `int`.
            KeyError: The given parameters lost degree of freedom.".

        Returns:
            tuple[str, dict[str, any]]: Current `expID` and arguments.
        """

        # wave
        wave1 = waveSelecter(self, wave1)
        wave2 = waveSelecter(self, wave2)

        # degree
        numQubits1 = self.waves[wave1].num_qubits
        numQubits2 = self.waves[wave2].num_qubits
        if numQubits1 != numQubits2:
            raise ValueError(
                f"Wave1 with {numQubits1} qubits and Wave2 with {numQubits2} qubits are different system size.")
        numQubits = numQubits1

        if degree is None:
            degree = numQubits
        degree = qubitSelector(numQubits, degree=degree)
        if measure is None:
            measure = numQubits
        measure = qubitSelector(
            numQubits, degree=measure, as_what='measure range')
        if unitary_set is None:
            unitary_set = numQubits
        unitary_set = qubitSelector(
            numQubits, degree=unitary_set, as_what='unitary_set')

        if (min(degree) < min(measure)) or (max(degree) > max(measure)):
            raise ValueError(
                f"Measure range '{measure}' does not contain subsystem '{degree}'.")
        if (min(measure) < min(unitary_set)) or (max(measure) > max(unitary_set)):
            raise ValueError(
                f"Unitary_set range '{unitary_set}' does not contain measure range '{measure}'.")

        # times
        if not isinstance(times, int):
            raise ValueError("'times' must be an 'int'.")
        elif times <= 0:
            raise ValueError("'times' must be larger than 0.")

        # expsName
        if expsName is None:
            expsName = f"w1={wave1}-w2={wave2}-deg={degree[1]-degree[0]}-at={times}.{self.shortName}"

        return (
            self.argsCore(**{
                'wave1': wave1,
                'wave2': wave2,
                'degree': degree,
                'times': times,

                'measure': measure,
                'unitary_set': unitary_set,
                'expsName': expsName,
            }),
            {
                k: v for k, v in otherArgs.items()
                if k not in self.argsCore._fields
            }
        )

    def method(
        self,
    ) -> list[QuantumCircuit]:
        """The method to construct circuit.
        Where should be overwritten by each construction of new measurement.

        Returns:
            list[QuantumCircuit]: The quantum circuit of experiment.
        """
        argsNow: Union[QurryV4.argsMain,
                       EchoHaarMeasureV4.argsCore] = self.now
        numQubits = self.waves[argsNow.wave1].num_qubits

        qcList: list[QuantumCircuit] = []
        unitaryList = [
            [random_unitary(2) for j in range(numQubits)]
            for i in range(argsNow.times)]

        ABegin = time.time()
        print(f"| Build circuit A: {argsNow.wave1}", end="\r")
        for i in range(argsNow.times):
            qFunc1 = QuantumRegister(numQubits, 'q1')
            cMeas1 = ClassicalRegister(
                argsNow.measure[1]-argsNow.measure[0], 'c1')
            qcExp1 = QuantumCircuit(qFunc1, cMeas1)

            qcExp1.append(self.waveCall(
                wave=argsNow.wave1,
                runBy=argsNow.runBy,
                backend=argsNow.backend,
            ), [qFunc1[i] for i in range(numQubits)])

            qcExp1.barrier()

            for j in range(*argsNow.unitary_set):
                qcExp1.append(unitaryList[i][j], [j])

            for j in range(*argsNow.measure):
                qcExp1.measure(qFunc1[j], cMeas1[j-argsNow.measure[0]])

            qcList.append(qcExp1)
            print(
                f"| Build circuit Add: {argsNow.wave1}" +
                f" - {i+1}/{argsNow.times} - {round(time.time() - ABegin, 3)}s.", end="\r")

        print(
            f"| Circuit A completed: {argsNow.wave1}" +
            f" - {i+1}/{argsNow.times} - {round(time.time() - ABegin, 3)}s." +
            " "*30)

        BBegin = time.time()
        print(f"| Build circuit B: {argsNow.wave2}", end="\r")
        for i in range(argsNow.times):
            qFunc2 = QuantumRegister(numQubits, 'q2')
            cMeas2 = ClassicalRegister(
                argsNow.measure[1]-argsNow.measure[0], 'c2')
            qcExp2 = QuantumCircuit(qFunc2, cMeas2)

            qcExp2.append(self.waveCall(
                wave=argsNow.wave2,
                runBy=argsNow.runBy,
                backend=argsNow.backend,
            ), [qFunc2[i] for i in range(numQubits)])

            qcExp2.barrier()

            for j in range(*argsNow.unitary_set):
                qcExp2.append(unitaryList[i][j], [j])

            for j in range(*argsNow.measure):
                qcExp2.measure(qFunc2[j], cMeas2[j-argsNow.measure[0]])

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
                for j in range(*argsNow.unitary_set)]
            for i in range(argsNow.times)}

        return qcList

    @classmethod
    def counts(
        cls,
        result: Union[Result, ManagedResults],
        resultIdxList: Optional[list[int]] = None,
        times: int = 0,
        **otherArgs,
    ):
        """Computing specific squantity.
        Where should be overwritten by each construction of new measurement.

        Returns:
            tuple[dict, dict]:
                Counts, echo, echo of experiment.
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
        for i in resultIdxList:
            try:
                allMeas = result.get_counts(i)
                counts.append(allMeas)
            except IBMQManagedResultDataNotAvailable as err:
                counts.append({})
                print("| Failed Job result skip, index:", i, err)
                continue

        return counts

    @classmethod
    def quantities(
        cls,
        shots: int,
        counts: list[Counts],
        times: int = 0,
        degree: tuple[int, int] = None,

        run_log: dict[str] = {},
        **otherArgs,
    ) -> expsCore:

        echo = -100
        echoCellList = []

        subsystemSize = max(degree) - min(degree)

        if (times*2 == len(counts)):
            ...
        else:
            times = len(counts)/2
            warnings.warn(
                f"times: {times} and counts number: {len(counts)} are different, use counts number," +
                "'times' = 0 is the default number.")

        Begin = time.time()

        for i in range(times):
            allMeas1 = counts[i]
            allMeas2 = counts[i+times]
            echoCell = 0

            allMeasUnderDegree1 = dict.fromkeys(
                [k[degree[0]:degree[1]] for k in allMeas1], 0)
            for kMeas in list(allMeas1):
                allMeasUnderDegree1[kMeas[degree[0]:degree[1]]] += allMeas1[kMeas]
            
            allMeasUnderDegree2 = dict.fromkeys(
                [k[degree[0]:degree[1]] for k in allMeas2], 0)
            for kMeas in list(allMeas2):
                allMeasUnderDegree2[kMeas[degree[0]:degree[1]]] += allMeas2[kMeas]
            
            numAllMeasUnderDegree = len(allMeasUnderDegree1)

            print(
                f"| Calculating overlap {i} and {i} " +
                f"by summarize {numAllMeasUnderDegree**2} values - {i+1}/{times}" +
                f" - {round(time.time() - Begin, 3)}s.", end="\r")
            for sAi, sAiMeas in allMeasUnderDegree1.items():
                for sAj, sAjMeas in allMeasUnderDegree2.items():
                    echoCell += cls.ensembleCell(
                        sAi, sAiMeas, sAj, sAjMeas, subsystemSize, shots)

            echoCellList.append(echoCell)
            print(
                f"| Calculating overlap end - {i+1}/{times}" +
                f" - {round(time.time() - Begin, 3)}s." +
                " "*30, end="\r")

        echo = np.mean(echoCellList)
        echoSD = np.std(echoCellList)
        
        quantity = {
            'echo': echo,
            'echoSD': echoSD,
            '_echoCellList': echoCellList,
        }
        return quantity

    def measure(
        self,
        wave1: Union[QuantumCircuit, any, None] = None,
        wave2: Union[QuantumCircuit, any, None] = None,
        degree: Union[int, tuple[int, int], None] = None,
        times: int = 100,
        measure: Union[int, tuple[int, int], None] = None,
        unitary_set: Union[int, tuple[int, int], None] = None,
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
            wave1=wave1,
            wave2=wave2,
            degree=degree,
            times=times,
            measure=measure,
            expsName=expsName,
            unitary_set=unitary_set,
            **otherArgs,
        )
