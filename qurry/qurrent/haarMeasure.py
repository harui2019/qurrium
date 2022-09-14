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

# EntropyMeasure V0.4.0 - Measuring Renyi Entropy - Qurrent


class EntropyHaarMeasureV4(QurryV4, haarBase):
    """HaarMeasure V0.4.0 of qurrent

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
        wave: Hashable = None
        degree: tuple[int, int] = None
        times: int = 100
        measure: tuple[int, int] = None
        unitary_set: tuple[int, int] = None

    class expsCore(NamedTuple):
        entropy: float
        purity: float
        puritySD: float
            
        sp_entropySD: float
        sp_entropy: float

    # Initialize
    def initialize(self) -> dict[str, any]:
        """Configuration to Initialize haarMeasure.

        Returns:
            dict[str, any]: The basic configuration of `haarMeasure`.
        """
        self._expsBase = defaultConfig(
            name='QurrentHaarBase',
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
            name='QurrentHaarMultiBase',
            default={
                **self.argsMultiMain()._asdict(),
                **self.expsMultiMain()._asdict(),
            },
        )

        self.shortName = 'qurrent_haar'
        self.__name__ = 'qurrent_haarMeasure'

    def paramsControlCore(
        self,
        expsName: Optional[str] = None,
        wave: Union[QuantumCircuit, any, None] = None,
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
        wave = waveSelecter(self, wave)

        # degree
        numQubits = self.waves[wave].num_qubits
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
            expsName = f"w={wave}-deg={degree[1]-degree[0]}-at={times}.{self.shortName}"

        return (
            self.argsCore(**{
                'wave': wave,
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
                       EntropyHaarMeasureV4.argsCore] = self.now
        numQubits = self.waves[argsNow.wave].num_qubits

        qcList = []
        unitaryList = [
            [random_unitary(2) for j in range(numQubits)]
            for i in range(argsNow.times)]

        ABegin = time.time()
        print(f"| Build circuit: {argsNow.wave}", end="\r")
        for i in range(argsNow.times):
            qFunc1 = QuantumRegister(numQubits, 'q1')
            cMeas1 = ClassicalRegister(
                argsNow.measure[1]-argsNow.measure[0], 'c1')
            qcExp1 = QuantumCircuit(qFunc1, cMeas1)

            qcExp1.append(self.waveCall(
                wave=argsNow.wave,
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
                f"| Build circuit: {argsNow.wave}" +
                f" - {i+1}/{argsNow.times} - {round(time.time() - ABegin, 3)}s.", end="\r")

        print(
            f"| Circuit completed: {argsNow.wave}" +
            f" - {i+1}/{argsNow.times} - {round(time.time() - ABegin, 3)}s." +
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
        degree: Union[tuple[int, int], int] = None,
        measure: tuple[int, int] = None,

        run_log: dict[str] = {},
        **otherArgs,
    ) -> expsCore:

        purity = -100
        entropy = -100
        purityCellList = []

        if isinstance(degree, int):
            subsystemSize = degree
            degree = qubitSelector(len(list(counts[0].keys())[0]), degree=degree)
        else:
            subsystemSize = max(degree) - min(degree)
            
        measureSize = max(measure) - min(measure)
        bitStringRange = (min(measure) - min(degree), max(degree) - min(degree))
        

        if (times == len(counts)):
            ...
        else:
            times = len(counts)
            warnings.warn(
                f"times: {times} and counts number: {len(counts)} are different, use counts number," +
                "'times' = 0 is the default number.")

        Begin = time.time()

        for i in range(times):
            allMeas1 = counts[i]
            purityCell = 0

            allMeasUnderDegree = dict.fromkeys(
                [k[bitStringRange[0]:bitStringRange[1]] for k in allMeas1], 0)
            for kMeas in list(allMeas1):
                allMeasUnderDegree[kMeas[bitStringRange[0]:bitStringRange[1]]] += allMeas1[kMeas]
            numAllMeasUnderDegree = len(allMeasUnderDegree)

            print(
                f"| Calculating overlap {i} and {i} " +
                f"by summarize {numAllMeasUnderDegree**2} values - {i+1}/{times}" +
                f" - {round(time.time() - Begin, 3)}s.", end="\r")
            for sAi, sAiMeas in allMeasUnderDegree.items():
                for sAj, sAjMeas in allMeasUnderDegree.items():
                    purityCell += cls.ensembleCell(
                        sAi, sAiMeas, sAj, sAjMeas, subsystemSize, shots)

            purityCellList.append(purityCell)
            print(
                f"| Calculating overlap end - {i+1}/{times}" +
                f" - {round(time.time() - Begin, 3)}s." +
                " "*30, end="\r")

        purity = np.mean(purityCellList)
        puritySD = np.std(purityCellList)
        
        entropy = -np.log2(purity)
        sp_entropyCellList = [-np.log2(X) for X in purityCellList]
        sp_entropySD = np.std(sp_entropyCellList)
        sp_entropy = np.mean(sp_entropyCellList)
        
        quantity = {
            'purity': purity,
            'entropy': entropy,
            
            '_purityCellList': purityCellList,
            'puritySD': puritySD,
            
            # '_sp_entropyCellList': sp_entropyCellList,
            # 'sp_entropySD': sp_entropySD,
            # 'sp_entropy': sp_entropy,
        }
        return quantity

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
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
            wave=wave,
            degree=degree,
            times=times,
            measure=measure,
            expsName=expsName,
            unitary_set=unitary_set,
            **otherArgs,
        )
